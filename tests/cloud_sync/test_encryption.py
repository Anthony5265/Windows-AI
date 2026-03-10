"""
Tests for Windows-AI Cloud Sync encryption module
"""

import pytest
import json
from windows_ai.cloud_sync.encryption import SyncEncryption, EncryptionKey


class TestSyncEncryption:
    """Test suite for SyncEncryption class"""

    def test_derive_key_from_password(self):
        """Test key derivation from password"""
        encryption = SyncEncryption(use_nacl=False)  # Use fallback for consistency
        password = "test_password_123"

        key1, salt1 = encryption.derive_key_from_password(password)
        assert len(key1) == 32  # 256-bit key
        assert len(salt1) >= 16  # Salt should be at least 16 bytes

        # Same password with same salt should produce same key
        key2, salt2 = encryption.derive_key_from_password(password, salt=salt1)
        assert key1 == key2
        assert salt1 == salt2

        # Different salt should produce different key
        key3, salt3 = encryption.derive_key_from_password(password)
        assert key1 != key3
        assert salt1 != salt3

    def test_create_key_from_password(self):
        """Test creating EncryptionKey from password"""
        encryption = SyncEncryption(use_nacl=False)
        password = "secure_password_456"

        key = encryption.create_key_from_password(password)

        assert isinstance(key, EncryptionKey)
        assert key.key_id is not None
        assert len(key.key_bytes) == 32
        assert len(key.salt) >= 16
        assert key.version == 1
        assert key.created_at != ""

    def test_encrypt_decrypt_data(self):
        """Test encryption and decryption of binary data"""
        encryption = SyncEncryption(use_nacl=False)
        password = "encryption_test_789"
        key = encryption.create_key_from_password(password)

        # Test with various data sizes
        test_data = [
            b"Hello, World!",
            b"A" * 1000,  # 1KB
            b"B" * 10000,  # 10KB
            bytes(range(256)),  # All byte values
        ]

        for data in test_data:
            encrypted = encryption.encrypt_data(data, key)
            assert encrypted != data
            assert len(encrypted) > len(data)  # Due to IV and MAC

            decrypted = encryption.decrypt_data(encrypted, key)
            assert decrypted == data

    def test_decrypt_with_wrong_key(self):
        """Test that decryption fails with wrong key"""
        encryption = SyncEncryption(use_nacl=False)
        key1 = encryption.create_key_from_password("password1")
        key2 = encryption.create_key_from_password("password2")

        data = b"Secret message"
        encrypted = encryption.encrypt_data(data, key1)

        with pytest.raises(ValueError):
            encryption.decrypt_data(encrypted, key2)

    def test_decrypt_tampered_data(self):
        """Test that decryption fails with tampered data"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("password")

        data = b"Original message"
        encrypted = encryption.encrypt_data(data, key)

        # Tamper with the encrypted data
        tampered = bytearray(encrypted)
        tampered[50] ^= 0xFF  # Flip bits
        tampered = bytes(tampered)

        with pytest.raises(ValueError):
            encryption.decrypt_data(tampered, key)

    def test_encrypt_decrypt_json(self):
        """Test encryption and decryption of JSON data"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("json_test")

        test_data = {
            "conversation_id": "abc123",
            "title": "Test Conversation",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "version": 1,
            "metadata": {"tags": ["important"], "pinned": True},
        }

        encrypted = encryption.encrypt_json(test_data, key)
        assert isinstance(encrypted, bytes)

        decrypted = encryption.decrypt_json(encrypted, key)
        assert decrypted == test_data

    def test_encrypt_to_base64(self):
        """Test encryption to base64 string"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("base64_test")

        data = b"Test data for base64"
        encrypted_b64 = encryption.encrypt_to_base64(data, key)

        assert isinstance(encrypted_b64, str)
        # Base64 should only contain valid characters
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in encrypted_b64)

        decrypted = encryption.decrypt_from_base64(encrypted_b64, key)
        assert decrypted == data

    def test_key_rotation(self):
        """Test key rotation"""
        encryption = SyncEncryption(use_nacl=False)
        old_key = encryption.create_key_from_password("old_password")
        new_key = encryption.rotate_key(old_key, "new_password")

        assert new_key.key_id != old_key.key_id
        assert new_key.key_bytes != old_key.key_bytes
        assert new_key.salt != old_key.salt

        # Data encrypted with old key should not decrypt with new key
        data = b"Test data"
        encrypted_old = encryption.encrypt_data(data, old_key)

        with pytest.raises(ValueError):
            encryption.decrypt_data(encrypted_old, new_key)

    def test_generate_key_backup(self):
        """Test generating encrypted key backup"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("main_password")
        backup_password = "backup_password_123"

        backup = encryption.generate_key_backup(key, backup_password)

        assert isinstance(backup, str)
        assert len(backup) > 100  # Should be substantial base64 string

    def test_restore_key_from_backup(self):
        """Test restoring key from backup"""
        encryption = SyncEncryption(use_nacl=False)
        original_key = encryption.create_key_from_password("main_password")
        backup_password = "backup_password_456"

        # Create backup
        backup = encryption.generate_key_backup(original_key, backup_password)

        # Restore from backup
        restored_key = encryption.restore_key_from_backup(backup, backup_password)

        assert restored_key.key_id == original_key.key_id
        assert restored_key.key_bytes == original_key.key_bytes
        assert restored_key.salt == original_key.salt
        assert restored_key.version == original_key.version

        # Data encrypted with original key should decrypt with restored key
        data = b"Test message"
        encrypted = encryption.encrypt_data(data, original_key)
        decrypted = encryption.decrypt_data(encrypted, restored_key)
        assert decrypted == data

    def test_restore_with_wrong_backup_password(self):
        """Test that restore fails with wrong backup password"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("main_password")
        backup = encryption.generate_key_backup(key, "correct_backup_password")

        with pytest.raises(ValueError):
            encryption.restore_key_from_backup(backup, "wrong_backup_password")

    def test_create_audit_hash(self):
        """Test creating audit hash"""
        encryption = SyncEncryption()
        data = b"Test data for hashing"

        hash1 = encryption.create_audit_hash(data)
        assert isinstance(hash1, str)
        assert len(hash1) > 40  # Base64 SHA-256 should be ~44 chars

        # Same data should produce same hash
        hash2 = encryption.create_audit_hash(data)
        assert hash1 == hash2

        # Different data should produce different hash
        hash3 = encryption.create_audit_hash(b"Different data")
        assert hash1 != hash3

    def test_verify_audit_hash(self):
        """Test verifying audit hash"""
        encryption = SyncEncryption()
        data = b"Test data"

        hash_val = encryption.create_audit_hash(data)
        assert encryption.verify_audit_hash(data, hash_val)

        # Tampered data should fail verification
        tampered_data = b"Tampered data"
        assert not encryption.verify_audit_hash(tampered_data, hash_val)

    def test_encryption_key_serialization(self):
        """Test EncryptionKey to_dict and from_dict"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("test_password")

        # Serialize to dict
        key_dict = key.to_dict()
        assert isinstance(key_dict, dict)
        assert "key_id" in key_dict
        assert "key_bytes" in key_dict
        assert "salt" in key_dict
        assert "version" in key_dict

        # Deserialize from dict
        restored_key = EncryptionKey.from_dict(key_dict)
        assert restored_key.key_id == key.key_id
        assert restored_key.key_bytes == key.key_bytes
        assert restored_key.salt == key.salt
        assert restored_key.version == key.version

    def test_large_data_encryption(self):
        """Test encryption of large data (1MB)"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("large_data_test")

        # 1MB of data
        large_data = b"X" * (1024 * 1024)

        encrypted = encryption.encrypt_data(large_data, key)
        decrypted = encryption.decrypt_data(encrypted, key)

        assert decrypted == large_data

    def test_unicode_json_encryption(self):
        """Test encryption of JSON with Unicode characters"""
        encryption = SyncEncryption(use_nacl=False)
        key = encryption.create_key_from_password("unicode_test")

        test_data = {
            "text": "Hello 世界 🌍",
            "symbols": "αβγδε",
            "emoji": "😀😃😄😁",
        }

        encrypted = encryption.encrypt_json(test_data, key)
        decrypted = encryption.decrypt_json(encrypted, key)

        assert decrypted == test_data

    def test_encode_base64(self):
        """Test standalone base64 encoding of raw bytes"""
        encryption = SyncEncryption(use_nacl=False)

        # Test basic encoding
        data = b"Hello, World!"
        encoded = encryption.encode_base64(data)
        assert isinstance(encoded, str)
        assert encoded == "SGVsbG8sIFdvcmxkIQ=="

        # Test empty bytes
        assert encryption.encode_base64(b"") == ""

        # Test binary data with all byte values
        binary_data = bytes(range(256))
        encoded_binary = encryption.encode_base64(binary_data)
        assert isinstance(encoded_binary, str)
        # Verify only valid base64 characters
        assert all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            for c in encoded_binary
        )

    def test_decode_base64(self):
        """Test standalone base64 decoding to raw bytes"""
        encryption = SyncEncryption(use_nacl=False)

        # Test basic decoding
        encoded = "SGVsbG8sIFdvcmxkIQ=="
        decoded = encryption.decode_base64(encoded)
        assert isinstance(decoded, bytes)
        assert decoded == b"Hello, World!"

        # Test empty string
        assert encryption.decode_base64("") == b""

        # Test roundtrip with various data
        test_data = [
            b"Simple ASCII text",
            b"\x00\x01\x02\xff\xfe\xfd",
            b"A" * 1000,
            bytes(range(256)),
        ]
        for data in test_data:
            encoded = encryption.encode_base64(data)
            decoded = encryption.decode_base64(encoded)
            assert decoded == data

    def test_encode_decode_base64_roundtrip(self):
        """Test that encode_base64 and decode_base64 are inverse operations"""
        encryption = SyncEncryption(use_nacl=False)

        # Test with encryption output
        key = encryption.create_key_from_password("roundtrip_test")
        original = b"Sensitive data for roundtrip test"
        encrypted = encryption.encrypt_data(original, key)

        # Encode the encrypted bytes to base64 and decode back
        b64 = encryption.encode_base64(encrypted)
        recovered = encryption.decode_base64(b64)
        assert recovered == encrypted

        # Verify the recovered encrypted data can still be decrypted
        decrypted = encryption.decrypt_data(recovered, key)
        assert decrypted == original


@pytest.fixture
def encryption():
    """Fixture providing SyncEncryption instance"""
    return SyncEncryption(use_nacl=False)


@pytest.fixture
def test_key(encryption):
    """Fixture providing test encryption key"""
    return encryption.create_key_from_password("test_fixture_password")
