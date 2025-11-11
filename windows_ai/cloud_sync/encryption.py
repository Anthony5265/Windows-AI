"""
End-to-end encryption for Windows-AI Cloud Sync using NaCl/libsodium

Implements zero-knowledge architecture where the server never sees plaintext data.
Uses Argon2id for key derivation and XSalsa20-Poly1305 for authenticated encryption.
"""

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

try:
    import nacl.secret
    import nacl.utils
    import nacl.pwhash
    from nacl.encoding import Base64Encoder
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False
    # Fallback implementation using standard library
    import hmac
    from itertools import cycle


@dataclass
class EncryptionKey:
    """Encryption key with metadata"""
    key_id: str
    key_bytes: bytes
    salt: bytes
    version: int = 1
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "key_bytes": base64.b64encode(self.key_bytes).decode(),
            "salt": base64.b64encode(self.salt).decode(),
            "version": self.version,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EncryptionKey":
        return cls(
            key_id=data["key_id"],
            key_bytes=base64.b64decode(data["key_bytes"]),
            salt=base64.b64decode(data["salt"]),
            version=data.get("version", 1),
            created_at=data.get("created_at", ""),
        )


class SyncEncryption:
    """
    Handles end-to-end encryption for cloud sync

    Uses NaCl (libsodium) with:
    - Argon2id for password-based key derivation
    - XSalsa20-Poly1305 for authenticated encryption
    - Zero-knowledge architecture
    """

    def __init__(self, use_nacl: bool = True):
        self.use_nacl = use_nacl and NACL_AVAILABLE
        if not self.use_nacl and use_nacl:
            print("Warning: PyNaCl not available, falling back to standard library encryption")

    def derive_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None,
        ops_limit: Optional[int] = None,
        mem_limit: Optional[int] = None,
    ) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using Argon2id

        Args:
            password: User's password
            salt: Optional salt (generated if not provided)
            ops_limit: Operations limit for Argon2id (defaults to MODERATE)
            mem_limit: Memory limit for Argon2id (defaults to MODERATE)

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            if self.use_nacl:
                salt = nacl.utils.random(nacl.pwhash.argon2id.SALTBYTES)
            else:
                salt = os.urandom(16)

        if self.use_nacl:
            # Use Argon2id via PyNaCl
            ops = ops_limit or nacl.pwhash.argon2id.OPSLIMIT_MODERATE
            mem = mem_limit or nacl.pwhash.argon2id.MEMLIMIT_MODERATE

            key = nacl.pwhash.argon2id.kdf(
                nacl.secret.SecretBox.KEY_SIZE,
                password.encode(),
                salt,
                opslimit=ops,
                memlimit=mem,
            )
        else:
            # Fallback to PBKDF2-HMAC-SHA256
            key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt,
                iterations=100000,
                dklen=32,
            )

        return key, salt

    def create_key_from_password(
        self,
        password: str,
        key_id: Optional[str] = None,
    ) -> EncryptionKey:
        """
        Create a new encryption key from a password

        Args:
            password: User's password
            key_id: Optional key ID (generated if not provided)

        Returns:
            EncryptionKey object
        """
        from datetime import datetime

        key_bytes, salt = self.derive_key_from_password(password)

        if key_id is None:
            key_id = base64.b64encode(os.urandom(16)).decode()[:16]

        return EncryptionKey(
            key_id=key_id,
            key_bytes=key_bytes,
            salt=salt,
            version=1,
            created_at=datetime.utcnow().isoformat(),
        )

    def encrypt_data(self, data: bytes, encryption_key: EncryptionKey) -> bytes:
        """
        Encrypt data using authenticated encryption

        Args:
            data: Plaintext data to encrypt
            encryption_key: EncryptionKey to use

        Returns:
            Encrypted data with authentication tag
        """
        if self.use_nacl:
            # Use NaCl SecretBox (XSalsa20-Poly1305)
            box = nacl.secret.SecretBox(encryption_key.key_bytes)
            encrypted = box.encrypt(data)
            return encrypted
        else:
            # Fallback implementation using HMAC and stream cipher
            return self._fallback_encrypt(data, encryption_key.key_bytes)

    def decrypt_data(self, encrypted_data: bytes, encryption_key: EncryptionKey) -> bytes:
        """
        Decrypt data and verify authentication tag

        Args:
            encrypted_data: Encrypted data with authentication tag
            encryption_key: EncryptionKey to use

        Returns:
            Decrypted plaintext data

        Raises:
            ValueError: If authentication fails or decryption fails
        """
        if self.use_nacl:
            # Use NaCl SecretBox (XSalsa20-Poly1305)
            box = nacl.secret.SecretBox(encryption_key.key_bytes)
            decrypted = box.decrypt(encrypted_data)
            return bytes(decrypted)
        else:
            # Fallback implementation
            return self._fallback_decrypt(encrypted_data, encryption_key.key_bytes)

    def encrypt_json(self, data: Dict[str, Any], encryption_key: EncryptionKey) -> bytes:
        """
        Encrypt JSON-serializable data

        Args:
            data: Dictionary to encrypt
            encryption_key: EncryptionKey to use

        Returns:
            Encrypted bytes
        """
        json_bytes = json.dumps(data, separators=(',', ':')).encode()
        return self.encrypt_data(json_bytes, encryption_key)

    def decrypt_json(self, encrypted_data: bytes, encryption_key: EncryptionKey) -> Dict[str, Any]:
        """
        Decrypt and parse JSON data

        Args:
            encrypted_data: Encrypted bytes
            encryption_key: EncryptionKey to use

        Returns:
            Decrypted dictionary

        Raises:
            ValueError: If decryption or JSON parsing fails
        """
        decrypted_bytes = self.decrypt_data(encrypted_data, encryption_key)
        return json.loads(decrypted_bytes.decode())

    def encrypt_to_base64(self, data: bytes, encryption_key: EncryptionKey) -> str:
        """Encrypt data and return as base64 string"""
        encrypted = self.encrypt_data(data, encryption_key)
        return base64.b64encode(encrypted).decode()

    def decrypt_from_base64(self, base64_data: str, encryption_key: EncryptionKey) -> bytes:
        """Decrypt data from base64 string"""
        encrypted = base64.b64decode(base64_data)
        return self.decrypt_data(encrypted, encryption_key)

    def rotate_key(
        self,
        old_key: EncryptionKey,
        new_password: str,
    ) -> EncryptionKey:
        """
        Create a new encryption key for key rotation

        Args:
            old_key: Current encryption key
            new_password: New password for the new key

        Returns:
            New EncryptionKey
        """
        return self.create_key_from_password(new_password)

    def _fallback_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Fallback encryption using standard library"""
        iv = os.urandom(16)
        keystream = self._keystream(key, iv, len(data))
        ciphertext = bytes(a ^ b for a, b in zip(data, keystream))
        mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
        return iv + mac + ciphertext

    def _fallback_decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Fallback decryption using standard library"""
        iv = encrypted_data[:16]
        mac = encrypted_data[16:48]
        ciphertext = encrypted_data[48:]

        expected_mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Authentication failed: MAC mismatch")

        keystream = self._keystream(key, iv, len(ciphertext))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
        return plaintext

    def _keystream(self, key: bytes, iv: bytes, length: int) -> bytes:
        """Generate keystream for fallback encryption"""
        out = bytearray()
        counter = 0
        while len(out) < length:
            ctr = counter.to_bytes(4, "big")
            out.extend(hmac.new(key, iv + ctr, hashlib.sha256).digest())
            counter += 1
        return bytes(out[:length])

    def generate_key_backup(
        self,
        encryption_key: EncryptionKey,
        backup_password: str,
    ) -> str:
        """
        Generate an encrypted backup of the encryption key

        Args:
            encryption_key: Key to backup
            backup_password: Password to encrypt the backup

        Returns:
            Base64-encoded encrypted key backup
        """
        backup_key, backup_salt = self.derive_key_from_password(backup_password)
        backup_enc_key = EncryptionKey(
            key_id="backup",
            key_bytes=backup_key,
            salt=backup_salt,
            version=1,
        )

        key_data = encryption_key.to_dict()
        encrypted_backup = self.encrypt_json(key_data, backup_enc_key)

        backup_package = {
            "backup_salt": base64.b64encode(backup_salt).decode(),
            "encrypted_key": base64.b64encode(encrypted_backup).decode(),
            "version": 1,
        }

        return base64.b64encode(json.dumps(backup_package).encode()).decode()

    def restore_key_from_backup(
        self,
        backup_data: str,
        backup_password: str,
    ) -> EncryptionKey:
        """
        Restore an encryption key from a backup

        Args:
            backup_data: Base64-encoded backup package
            backup_password: Password used to encrypt the backup

        Returns:
            Restored EncryptionKey

        Raises:
            ValueError: If backup is invalid or password is wrong
        """
        try:
            backup_package = json.loads(base64.b64decode(backup_data))
            backup_salt = base64.b64decode(backup_package["backup_salt"])
            encrypted_key = base64.b64decode(backup_package["encrypted_key"])

            backup_key, _ = self.derive_key_from_password(backup_password, salt=backup_salt)
            backup_enc_key = EncryptionKey(
                key_id="backup",
                key_bytes=backup_key,
                salt=backup_salt,
                version=1,
            )

            key_data = self.decrypt_json(encrypted_key, backup_enc_key)
            return EncryptionKey.from_dict(key_data)
        except Exception as e:
            raise ValueError(f"Failed to restore key from backup: {e}")

    def create_audit_hash(self, data: bytes) -> str:
        """
        Create a hash of encrypted data for audit trail

        Args:
            data: Data to hash

        Returns:
            Base64-encoded SHA-256 hash
        """
        hash_obj = hashlib.sha256(data)
        return base64.b64encode(hash_obj.digest()).decode()

    def verify_audit_hash(self, data: bytes, expected_hash: str) -> bool:
        """
        Verify data against an audit hash

        Args:
            data: Data to verify
            expected_hash: Expected hash value

        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = self.create_audit_hash(data)
        return hmac.compare_digest(actual_hash, expected_hash)
