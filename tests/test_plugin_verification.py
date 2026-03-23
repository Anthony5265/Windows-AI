"""Tests for plugin signature verification."""
import pytest
import tempfile
import os
from pathlib import Path

from windows_ai.security.plugin_verification import (
    PluginSignatureVerifier,
    PluginSignature,
)


@pytest.fixture
def verifier(tmp_path):
    """Create verifier with temp directory."""
    return PluginSignatureVerifier(signatures_dir=tmp_path / "sigs")


@pytest.fixture
def plugin_file(tmp_path):
    """Create a temporary plugin file."""
    plugin = tmp_path / "test_plugin.py"
    plugin.write_text('"""Test plugin"""\nclass TestPlugin:\n    pass\n')
    return str(plugin)


class TestPluginSignatureVerifier:
    """Test plugin signature verification."""

    def test_compute_hash(self, plugin_file):
        """compute_hash returns consistent SHA-256."""
        hash1 = PluginSignatureVerifier.compute_hash(plugin_file)
        hash2 = PluginSignatureVerifier.compute_hash(plugin_file)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_sign_plugin(self, verifier, plugin_file):
        """Can sign a plugin file."""
        sig = verifier.sign_plugin(plugin_file)
        assert sig.plugin_id == "test_plugin"
        assert len(sig.file_hash) == 64
        assert sig.file_size > 0
        assert sig.verified is True

    def test_verify_plugin_valid(self, verifier, plugin_file):
        """Signed plugin verifies correctly."""
        verifier.sign_plugin(plugin_file)
        assert verifier.verify_plugin(plugin_file) is True

    def test_verify_plugin_tampered(self, verifier, plugin_file):
        """Tampered plugin fails verification."""
        verifier.sign_plugin(plugin_file)

        # Tamper with the file
        with open(plugin_file, "a") as f:
            f.write("\n# malicious code\n")

        assert verifier.verify_plugin(plugin_file) is False

    def test_verify_unsigned_plugin(self, verifier, plugin_file):
        """Unsigned plugin returns False."""
        assert verifier.verify_plugin(plugin_file) is False

    def test_verify_missing_file(self, verifier):
        """Missing file returns False."""
        assert verifier.verify_plugin("/nonexistent/file.py") is False

    def test_sign_nonexistent_file(self, verifier):
        """Signing nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            verifier.sign_plugin("/nonexistent/file.py")

    def test_sign_directory(self, verifier, tmp_path):
        """Can sign all plugins in a directory."""
        # Create some test plugin files
        for i in range(3):
            (tmp_path / f"plugin_{i}.py").write_text(f'"""Plugin {i}"""\npass\n')
        (tmp_path / "__init__.py").write_text("")  # Should be skipped

        sigs = verifier.sign_directory(str(tmp_path))
        assert len(sigs) == 3

    def test_verify_directory(self, verifier, tmp_path):
        """Can verify all plugins in a directory."""
        for i in range(3):
            (tmp_path / f"plugin_{i}.py").write_text(f'"""Plugin {i}"""\npass\n')

        verifier.sign_directory(str(tmp_path))
        results = verifier.verify_directory(str(tmp_path))
        assert all(results.values())
        assert len(results) == 3

    def test_get_signature(self, verifier, plugin_file):
        """Can retrieve stored signature."""
        verifier.sign_plugin(plugin_file)
        sig = verifier.get_signature("test_plugin")
        assert sig is not None
        assert "file_hash" in sig
        assert "signer" in sig

    def test_list_signed_plugins(self, verifier, plugin_file):
        """Can list all signed plugins."""
        verifier.sign_plugin(plugin_file)
        signed = verifier.list_signed_plugins()
        assert "test_plugin" in signed

    def test_remove_signature(self, verifier, plugin_file):
        """Can remove a stored signature."""
        verifier.sign_plugin(plugin_file)
        assert verifier.remove_signature("test_plugin") is True
        assert verifier.get_signature("test_plugin") is None

    def test_remove_nonexistent(self, verifier):
        """Removing nonexistent signature returns False."""
        assert verifier.remove_signature("nonexistent") is False

    def test_stats(self, verifier, plugin_file):
        """Stats returns correct info."""
        verifier.sign_plugin(plugin_file)
        stats = verifier.stats()
        assert stats["total_signed"] == 1

    def test_persistence(self, tmp_path, plugin_file):
        """Signatures persist across verifier instances."""
        sig_dir = tmp_path / "sigs"

        # Sign with first instance
        v1 = PluginSignatureVerifier(signatures_dir=sig_dir)
        v1.sign_plugin(plugin_file)

        # Verify with second instance
        v2 = PluginSignatureVerifier(signatures_dir=sig_dir)
        assert v2.verify_plugin(plugin_file) is True
