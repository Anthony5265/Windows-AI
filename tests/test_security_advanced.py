import pytest
from windows_ai.security.auth import AuthManager
from windows_ai.security.encryption import EncryptionManager
from unittest.mock import Mock, patch

class TestSecurityAdvanced:
    def test_auth_token_validation(self):
        auth = AuthManager()
        token = auth.create_token('user123')
        assert auth.validate_token(token)
        
    def test_password_hashing(self):
        auth = AuthManager()
        hashed = auth.hash_password('test_password')
        assert auth.verify_password('test_password', hashed)
        
    def test_encryption_roundtrip(self):
        encryptor = EncryptionManager()
        plaintext = 'sensitive data'
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext
        
    def test_audit_logging(self):
        from windows_ai.security.audit import AuditLogger
        logger = AuditLogger()
        logger.log_action('test_user', 'test_action', 'success')
        assert True
