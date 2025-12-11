"""
Credential Manager for Windows AI

Secure storage and retrieval of API keys, tokens, and credentials using:
- Windows Credential Manager (win32cred) on Windows
- Encrypted JSON fallback for cross-platform support
- Environment variable support for development
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import win32cred
    import win32con
    WINDOWS_CRED_AVAILABLE = True
except ImportError:
    WINDOWS_CRED_AVAILABLE = False

from windows_ai.cloud_sync.encryption import SyncEncryption

logger = logging.getLogger(__name__)


@dataclass
class Credential:
    """Represents a stored credential"""
    service_id: str
    key_name: str
    key_value: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    last_used: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Credential":
        """Create from dictionary"""
        return cls(**data)


class CredentialManager:
    """
    Manages secure storage and retrieval of credentials
    
    Storage priority:
    1. Windows Credential Manager (if available)
    2. Encrypted JSON file
    3. Environment variables (read-only)
    """
    
    def __init__(self, encryption_password: Optional[str] = None):
        self.use_windows_cred = WINDOWS_CRED_AVAILABLE
        self.encryption = SyncEncryption(use_nacl=True)
        self.encryption_password = encryption_password or self._get_default_password()
        self.cache: Dict[str, Credential] = {}
        
        # Derive encryption key for file storage
        self.encryption_key, self.salt = self.encryption.derive_key_from_password(
            self.encryption_password
        )
        
        # Storage path for encrypted credentials
        self.storage_path = Path.home() / ".windows_ai" / "credentials.enc"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Credential Manager initialized (Windows Cred: {self.use_windows_cred})")
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the credential manager
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            # Load cached credentials from storage
            await self.load_credentials()
            self._initialized = True
            logger.info("Credential Manager fully initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize credential manager: {e}")
            return False
    
    async def load_credentials(self) -> Dict[str, Credential]:
        """Load all credentials from storage
        
        Returns:
            Dictionary of credentials keyed by service:key
        """
        # Load from encrypted file if it exists
        if self.storage_path.exists():
            try:
                credentials = self._load_encrypted_credentials()
                self.cache.update(credentials)
            except Exception as e:
                logger.error(f"Failed to load encrypted credentials: {e}")
        
        # Load from environment variables as fallback
        env_credentials = self._load_env_credentials()
        self.cache.update(env_credentials)
        
        return self.cache
    
    def _load_env_credentials(self) -> Dict[str, Credential]:
        """Load credentials from environment variables"""
        credentials = {}
        
        # Standard API key environment variables
        env_mappings = {
            "OPENAI_API_KEY": ("openai", "api_key"),
            "ANTHROPIC_API_KEY": ("anthropic", "api_key"),
            "GOOGLE_API_KEY": ("google", "api_key"),
            "AZURE_OPENAI_API_KEY": ("azure", "api_key"),
            "MISTRAL_API_KEY": ("mistral", "api_key"),
            "GROQ_API_KEY": ("groq", "api_key"),
            "COHERE_API_KEY": ("cohere", "api_key"),
            "REPLICATE_API_TOKEN": ("replicate", "api_key"),
            "HUGGINGFACE_API_KEY": ("huggingface", "api_key"),
        }
        
        for env_var, (service, key_name) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                cred_key = f"{service}:{key_name}"
                credentials[cred_key] = Credential(
                    service_id=service,
                    key_name=key_name,
                    key_value=value,
                    description=f"Loaded from {env_var}"
                )
        
        return credentials
    
    def get_credential(self, key_or_service: str, key_name: Optional[str] = None) -> Optional[str]:
        """Get a credential value
        
        Args:
            key_or_service: Either 'service:key' format or service ID
            key_name: Key name if service ID provided separately
            
        Returns:
            Credential value or None if not found
        """
        if key_name:
            cache_key = f"{key_or_service}:{key_name}"
        else:
            # Check if it's an environment variable name
            if key_or_service in os.environ:
                return os.environ[key_or_service]
            cache_key = key_or_service
        
        credential = self.cache.get(cache_key)
        if credential:
            credential.last_used = datetime.now().isoformat()
            return credential.key_value
        
        return None
    
    def _get_default_password(self) -> str:
        """Get default encryption password based on machine ID"""
        import platform
        import hashlib
        machine_id = platform.node() + platform.machine()
        return hashlib.sha256(machine_id.encode()).hexdigest()
    
    def _get_target_name(self, service_id: str, key_name: str) -> str:
        """Generate Windows Credential Manager target name"""
        return f"WindowsAI:{service_id}:{key_name}"
    
    async def store_credential(
        self,
        service_id: str,
        key_name: str,
        key_value: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Store a credential securely
        
        Args:
            service_id: ID of the service/plugin (e.g., "openai", "github")
            key_name: Name of the credential (e.g., "api_key", "token")
            key_value: The actual credential value
            description: Optional description
            
        Returns:
            True if stored successfully
        """
        try:
            credential = Credential(
                service_id=service_id,
                key_name=key_name,
                key_value=key_value,
                description=description
            )
            
            # Try Windows Credential Manager first
            if self.use_windows_cred:
                success = self._store_windows_credential(credential)
                if success:
                    self.cache[f"{service_id}:{key_name}"] = credential
                    logger.debug(f"Stored credential in Windows Credential Manager: {service_id}:{key_name}")
                    return True
            
            # Fall back to encrypted file storage
            success = self._store_encrypted_credential(credential)
            if success:
                self.cache[f"{service_id}:{key_name}"] = credential
                logger.debug(f"Stored credential in encrypted file: {service_id}:{key_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to store credential {service_id}:{key_name}: {e}")
            return False
    
    def _store_windows_credential(self, credential: Credential) -> bool:
        """Store credential in Windows Credential Manager"""
        if not self.use_windows_cred:
            return False
        
        try:
            target_name = self._get_target_name(credential.service_id, credential.key_name)
            
            # Create credential object
            cred = {
                'Type': win32cred.CRED_TYPE_GENERIC,
                'TargetName': target_name,
                'CredentialBlob': credential.key_value,
                'Comment': credential.description or f"Windows AI - {credential.service_id}",
                'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE
            }
            
            # Write to Windows Credential Manager
            win32cred.CredWrite(cred, 0)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in Windows Credential Manager: {e}")
            return False
    
    def _store_encrypted_credential(self, credential: Credential) -> bool:
        """Store credential in encrypted JSON file"""
        try:
            # Load existing credentials
            credentials = self._load_encrypted_credentials()
            
            # Add or update credential
            key = f"{credential.service_id}:{credential.key_name}"
            credentials[key] = credential.to_dict()
            
            # Encrypt and save
            plaintext = json.dumps(credentials, indent=2)
            
            if self.encryption.use_nacl:
                import nacl.secret
                box = nacl.secret.SecretBox(self.encryption_key)
                nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
                ciphertext = box.encrypt(plaintext.encode(), nonce)
                encrypted_data = {
                    'version': 1,
                    'salt': self.encryption.encode_base64(self.salt),
                    'data': self.encryption.encode_base64(ciphertext)
                }
            else:
                # Fallback XOR encryption
                encrypted_data = {
                    'version': 0,
                    'salt': self.encryption.encode_base64(self.salt),
                    'data': self._xor_encrypt(plaintext, self.encryption_key)
                }
            
            # Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(encrypted_data, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in encrypted file: {e}")
            return False
    
    def _load_encrypted_credentials(self) -> Dict[str, Dict[str, Any]]:
        """Load credentials from encrypted file"""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                encrypted_data = json.load(f)
            
            version = encrypted_data.get('version', 0)
            
            if version == 1 and self.encryption.use_nacl:
                # Decrypt with NaCl
                import nacl.secret
                box = nacl.secret.SecretBox(self.encryption_key)
                ciphertext = self.encryption.decode_base64(encrypted_data['data'])
                plaintext = box.decrypt(ciphertext).decode()
            else:
                # Fallback XOR decryption
                plaintext = self._xor_decrypt(
                    encrypted_data['data'],
                    self.encryption_key
                )
            
            return json.loads(plaintext)
            
        except Exception as e:
            logger.error(f"Failed to load encrypted credentials: {e}")
            return {}
    
    def _xor_encrypt(self, plaintext: str, key: bytes) -> str:
        """Simple XOR encryption fallback"""
        import base64
        from itertools import cycle
        encrypted = bytes(a ^ b for a, b in zip(plaintext.encode(), cycle(key)))
        return base64.b64encode(encrypted).decode()
    
    def _xor_decrypt(self, ciphertext: str, key: bytes) -> str:
        """Simple XOR decryption fallback"""
        import base64
        from itertools import cycle
        encrypted = base64.b64decode(ciphertext)
        decrypted = bytes(a ^ b for a, b in zip(encrypted, cycle(key)))
        return decrypted.decode()
    
    async def get_credential(
        self,
        service_id: str,
        key_name: str,
        check_env: bool = True
    ) -> Optional[str]:
        """
        Retrieve a credential
        
        Args:
            service_id: ID of the service/plugin
            key_name: Name of the credential
            check_env: Whether to check environment variables as fallback
            
        Returns:
            Credential value or None if not found
        """
        try:
            # Check cache first
            cache_key = f"{service_id}:{key_name}"
            if cache_key in self.cache:
                credential = self.cache[cache_key]
                credential.last_used = datetime.now().isoformat()
                return credential.key_value
            
            # Try Windows Credential Manager
            if self.use_windows_cred:
                value = self._get_windows_credential(service_id, key_name)
                if value:
                    return value
            
            # Try encrypted file storage
            value = self._get_encrypted_credential(service_id, key_name)
            if value:
                return value
            
            # Fall back to environment variables
            if check_env:
                env_var = f"{service_id.upper()}_{key_name.upper()}"
                value = os.getenv(env_var)
                if value:
                    logger.debug(f"Retrieved credential from environment: {env_var}")
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential {service_id}:{key_name}: {e}")
            return None
    
    def _get_windows_credential(self, service_id: str, key_name: str) -> Optional[str]:
        """Retrieve credential from Windows Credential Manager"""
        if not self.use_windows_cred:
            return None
        
        try:
            target_name = self._get_target_name(service_id, key_name)
            cred = win32cred.CredRead(
                TargetName=target_name,
                Type=win32cred.CRED_TYPE_GENERIC
            )
            return cred['CredentialBlob'].decode()
            
        except Exception:
            return None
    
    def _get_encrypted_credential(self, service_id: str, key_name: str) -> Optional[str]:
        """Retrieve credential from encrypted file"""
        try:
            credentials = self._load_encrypted_credentials()
            key = f"{service_id}:{key_name}"
            if key in credentials:
                return credentials[key]['key_value']
            return None
        except Exception:
            return None
    
    async def delete_credential(self, service_id: str, key_name: str) -> bool:
        """
        Delete a credential
        
        Args:
            service_id: ID of the service/plugin
            key_name: Name of the credential
            
        Returns:
            True if deleted successfully
        """
        try:
            # Remove from cache
            cache_key = f"{service_id}:{key_name}"
            self.cache.pop(cache_key, None)
            
            # Delete from Windows Credential Manager
            if self.use_windows_cred:
                self._delete_windows_credential(service_id, key_name)
            
            # Delete from encrypted file
            self._delete_encrypted_credential(service_id, key_name)
            
            logger.debug(f"Deleted credential: {service_id}:{key_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credential {service_id}:{key_name}: {e}")
            return False
    
    def _delete_windows_credential(self, service_id: str, key_name: str) -> bool:
        """Delete credential from Windows Credential Manager"""
        if not self.use_windows_cred:
            return False
        
        try:
            target_name = self._get_target_name(service_id, key_name)
            win32cred.CredDelete(
                TargetName=target_name,
                Type=win32cred.CRED_TYPE_GENERIC
            )
            return True
        except Exception:
            return False
    
    def _delete_encrypted_credential(self, service_id: str, key_name: str) -> bool:
        """Delete credential from encrypted file"""
        try:
            credentials = self._load_encrypted_credentials()
            key = f"{service_id}:{key_name}"
            if key in credentials:
                del credentials[key]
                
                # Save updated credentials
                plaintext = json.dumps(credentials, indent=2)
                
                if self.encryption.use_nacl:
                    import nacl.secret
                    box = nacl.secret.SecretBox(self.encryption_key)
                    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
                    ciphertext = box.encrypt(plaintext.encode(), nonce)
                    encrypted_data = {
                        'version': 1,
                        'salt': self.encryption.encode_base64(self.salt),
                        'data': self.encryption.encode_base64(ciphertext)
                    }
                else:
                    encrypted_data = {
                        'version': 0,
                        'salt': self.encryption.encode_base64(self.salt),
                        'data': self._xor_encrypt(plaintext, self.encryption_key)
                    }
                
                with open(self.storage_path, 'w') as f:
                    json.dump(encrypted_data, f)
            
            return True
        except Exception:
            return False
    
    async def list_credentials(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List stored credentials
        
        Args:
            service_id: Optional filter by service ID
            
        Returns:
            List of credential metadata (without values)
        """
        try:
            credentials = self._load_encrypted_credentials()
            result = []
            
            for key, cred_data in credentials.items():
                if service_id and not key.startswith(f"{service_id}:"):
                    continue
                
                # Don't include the actual key value
                result.append({
                    'service_id': cred_data['service_id'],
                    'key_name': cred_data['key_name'],
                    'description': cred_data.get('description'),
                    'created_at': cred_data.get('created_at'),
                    'last_used': cred_data.get('last_used')
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list credentials: {e}")
            return []
    
    async def update_credential(
        self,
        service_id: str,
        key_name: str,
        new_value: str
    ) -> bool:
        """
        Update an existing credential
        
        Args:
            service_id: ID of the service/plugin
            key_name: Name of the credential
            new_value: New credential value
            
        Returns:
            True if updated successfully
        """
        # Get existing credential to preserve metadata
        credentials = self._load_encrypted_credentials()
        key = f"{service_id}:{key_name}"
        
        description = None
        if key in credentials:
            description = credentials[key].get('description')
        
        # Store with new value
        return await self.store_credential(
            service_id=service_id,
            key_name=key_name,
            key_value=new_value,
            description=description
        )
