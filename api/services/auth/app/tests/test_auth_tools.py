import pytest
from authentication.tools import PasswordTools, TokenTools
from datetime import datetime, timedelta
import jwt
import os

class TestPasswordTools:
    def setup_method(self):
        self.password_tools = PasswordTools()

    def test_encode_password_valid(self):
        password = "securepassword123"
        hashed = self.password_tools.encode_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password

    def test_encode_password_none(self):
        with pytest.raises(ValueError, match="password cannot be None"):
            self.password_tools.encode_password(None)

    def test_verify_password_correct(self):
        password = "securepassword123"
        hashed = self.password_tools.encode_password(password)
        
        assert self.password_tools.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "securepassword123"
        wrong_password = "wrongpassword"
        hashed = self.password_tools.encode_password(password)
        
        assert self.password_tools.verify_password(wrong_password, hashed) is False

    def test_verify_password_none_password(self):
        with pytest.raises(ValueError, match="password cannot be None"):
            self.password_tools.verify_password(None, "somehash")

    def test_verify_password_invalid_hash(self):
        with pytest.raises(ValueError, match="Invalid hashed password"):
            self.password_tools.verify_password("password", "")

    def test_verify_password_malformed_hash(self):
        with pytest.raises(ValueError, match="Invalid hashed password format"):
            self.password_tools.verify_password("password", "invalid_hash_format")


class TestTokenTools:
    def setup_method(self):
        self.token_tools = TokenTools()
        self.sample_payload = {"user_id": 123, "username": "testuser"}

    def test_create_access_token_valid(self):
        token = self.token_tools.create_access_token(self.sample_payload)
        
        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_none_payload(self):
        with pytest.raises(ValueError, match="user data cannot be None"):
            self.token_tools.create_access_token(None)

    def test_create_refresh_token_valid(self):
        token = self.token_tools.create_refresh_token(self.sample_payload)
        
        assert token is not None
        assert isinstance(token, str)

    def test_validate_token_valid_access(self):
        token = self.token_tools.create_access_token(self.sample_payload)
        assert self.token_tools.validate_token(token, "access") is True

    def test_validate_token_valid_refresh(self):
        token = self.token_tools.create_refresh_token(self.sample_payload)
        assert self.token_tools.validate_token(token, "refresh") is True

    def test_validate_token_wrong_type(self):
        token = self.token_tools.create_access_token(self.sample_payload)
        assert self.token_tools.validate_token(token, "refresh") is False

    def test_validate_token_none(self):
        with pytest.raises(ValueError, match="Token cannot be None"):
            self.token_tools.validate_token(None)

    def test_validate_token_invalid(self):
        assert self.token_tools.validate_token("invalid_token") is False

    def test_get_token_payload_valid(self):
        token = self.token_tools.create_access_token(self.sample_payload)
        payload = self.token_tools.get_token_payload(token)
        
        assert payload == self.sample_payload
        assert "expiration" not in payload
        assert "issued_at" not in payload
        assert "type" not in payload

    def test_get_token_payload_none(self):
        with pytest.raises(ValueError, match="Token cannot be None"):
            self.token_tools.get_token_payload(None)

    def test_get_token_payload_empty(self):
        with pytest.raises(ValueError, match="Token cannot be empty"):
            self.token_tools.get_token_payload("")

    def test_get_token_payload_expired(self):
        # Create an expired token manually
        expired_time = datetime.now() - timedelta(hours=1)
        issued_time = datetime.now() - timedelta(hours=2)
    
        expired_payload = {
            **self.sample_payload,
            'expiration': expired_time.timestamp(),
            'issued_at': issued_time.timestamp(),
            'type': 'access'
        }
        JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'random-secret-key')
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, 'HS256')
        
        with pytest.raises(ValueError, match="Token has expired"):
            self.token_tools.get_token_payload(expired_token)

    def test_refresh_access_token_valid(self):
        refresh_token = self.token_tools.create_refresh_token(self.sample_payload)
        new_access_token = self.token_tools.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        assert isinstance(new_access_token, str)
        assert self.token_tools.validate_token(new_access_token, "access") is True

    def test_refresh_access_token_empty(self):
        with pytest.raises(ValueError, match="Refresh token cannot be empty"):
            self.token_tools.refresh_access_token("")

    def test_refresh_access_token_invalid(self):
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            self.token_tools.refresh_access_token("invalid_token")

    def test_refresh_access_token_wrong_type(self):
        access_token = self.token_tools.create_access_token(self.sample_payload)
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            self.token_tools.refresh_access_token(access_token)

    def test_token_payload_structure(self):
        token = self.token_tools.create_access_token(self.sample_payload)
        decoded = jwt.decode(token, 'random-secret-key', 'HS256')
        
        assert 'expiration' in decoded
        assert 'issued_at' in decoded
        assert 'type' in decoded
        assert decoded['type'] == 'access'
        assert decoded['user_id'] == 123
        assert decoded['username'] == 'testuser'