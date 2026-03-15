"""
Plugin Signature Verification

Provides cryptographic verification for plugins to ensure they haven't been
tampered with. Uses SHA-256 hashing to verify plugin integrity.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Directory for signature storage
SIGNATURES_DIR = Path.home() / ".windows_ai" / "signatures"


@dataclass
class PluginSignature:
    """Represents a plugin's signature."""
    plugin_id: str
    file_hash: str
    file_size: int
    signed_at: str
    signer: str
    verified: bool = False


class PluginSignatureVerifier:
    """
    Verifies plugin integrity using cryptographic hashes.
    
    Features:
    - SHA-256 hash computation for plugin files
    - Signature storage and retrieval
    - Batch verification of all plugins
    - Tamper detection
    
    Usage:
        verifier = PluginSignatureVerifier()
        
        # Sign a plugin
        sig = verifier.sign_plugin("path/to/plugin.py")
        
        # Verify a plugin
        is_valid = verifier.verify_plugin("path/to/plugin.py")
    """

    def __init__(self, signatures_dir: Optional[Path] = None):
        self._signatures_dir = signatures_dir or SIGNATURES_DIR
        self._signatures_dir.mkdir(parents=True, exist_ok=True)
        self._signatures_file = self._signatures_dir / "plugin_signatures.json"
        self._signatures: Dict[str, Dict[str, Any]] = self._load_signatures()

    def _load_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Load signatures from storage."""
        if self._signatures_file.exists():
            try:
                with open(self._signatures_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load signatures: {e}")
        return {}

    def _save_signatures(self):
        """Save signatures to storage."""
        with open(self._signatures_file, "w") as f:
            json.dump(self._signatures, f, indent=2)

    @staticmethod
    def compute_hash(file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def sign_plugin(self, file_path: str, signer: str = "Windows AI Team") -> PluginSignature:
        """
        Sign a plugin file by computing and storing its hash.
        
        Args:
            file_path: Path to the plugin file
            signer: Identity of the signer
            
        Returns:
            PluginSignature with the computed hash
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {file_path}")

        file_hash = self.compute_hash(file_path)
        file_size = path.stat().st_size
        signed_at = str(__import__("datetime").datetime.now())

        plugin_id = path.stem
        sig = PluginSignature(
            plugin_id=plugin_id,
            file_hash=file_hash,
            file_size=file_size,
            signed_at=signed_at,
            signer=signer,
            verified=True,
        )

        self._signatures[plugin_id] = {
            "file_hash": file_hash,
            "file_size": file_size,
            "file_path": str(path.absolute()),
            "signed_at": signed_at,
            "signer": signer,
        }
        self._save_signatures()
        logger.info(f"Plugin '{plugin_id}' signed: {file_hash[:16]}...")

        return sig

    def verify_plugin(self, file_path: str) -> bool:
        """
        Verify a plugin file against its stored signature.
        
        Returns True if the file hash matches the stored signature.
        Returns False if no signature exists or hash doesn't match.
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Plugin file not found: {file_path}")
            return False

        plugin_id = path.stem
        stored = self._signatures.get(plugin_id)
        if not stored:
            logger.debug(f"No signature found for plugin: {plugin_id}")
            return False

        current_hash = self.compute_hash(file_path)
        expected_hash = stored["file_hash"]

        if current_hash == expected_hash:
            logger.debug(f"Plugin '{plugin_id}' verification: PASSED")
            return True
        else:
            logger.warning(
                f"Plugin '{plugin_id}' verification: FAILED "
                f"(expected {expected_hash[:16]}, got {current_hash[:16]})"
            )
            return False

    def sign_directory(self, directory: str, signer: str = "Windows AI Team") -> List[PluginSignature]:
        """Sign all plugin files in a directory."""
        results = []
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        for plugin_file in sorted(dir_path.rglob("*.py")):
            if plugin_file.name.startswith("_"):
                continue
            try:
                sig = self.sign_plugin(str(plugin_file), signer)
                results.append(sig)
            except Exception as e:
                logger.error(f"Failed to sign {plugin_file}: {e}")

        logger.info(f"Signed {len(results)} plugins in {directory}")
        return results

    def verify_directory(self, directory: str) -> Dict[str, bool]:
        """Verify all plugin files in a directory."""
        results = {}
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        for plugin_file in sorted(dir_path.rglob("*.py")):
            if plugin_file.name.startswith("_"):
                continue
            results[plugin_file.stem] = self.verify_plugin(str(plugin_file))

        valid = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"Verified {valid}/{total} plugins in {directory}")
        return results

    def get_signature(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get stored signature for a plugin."""
        return self._signatures.get(plugin_id)

    def list_signed_plugins(self) -> List[str]:
        """List all signed plugin IDs."""
        return list(self._signatures.keys())

    def remove_signature(self, plugin_id: str) -> bool:
        """Remove a stored signature."""
        if plugin_id in self._signatures:
            del self._signatures[plugin_id]
            self._save_signatures()
            return True
        return False

    def stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        return {
            "total_signed": len(self._signatures),
            "signatures_dir": str(self._signatures_dir),
        }
