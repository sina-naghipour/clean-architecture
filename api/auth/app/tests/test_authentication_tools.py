import pytest
from authentication.tools import (
    encode_password,
    verify_password,
    validate_token,
    create_token,
    refresh_token,
    revoke_token,
    get_token_payload
)


class TestEncodePassword:
    
    def test_encode_password_success(self):
        result = encode_password("my_secure_password")
        
        assert result is not None
        assert isinstance(result, str)
        assert result != "my_secure_password"
        assert len(result) > 0
    
    def test_encode_password_empty_string(self):
        result = encode_password("")
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_encode_password_none(self):
        with pytest.raises(ValueError):
            encode_password(None)
    
    def test_encode_password_special_characters(self):
        complex_password = "P@ssw0rd!@#$%^&*()"
        result = encode_password(complex_password)
        
        assert result is not None
        assert isinstance(result, str)
        assert result != complex_password


class TestVerifyPassword:
    
    def test_verify_password_success(self):
        plain_password = "test_password"
        hashed_password = encode_password(plain_password)
        result = verify_password(plain_password, hashed_password)
        
        assert result is True
    
    def test_verify_password_wrong_password(self):
        hashed_password = encode_password("correct_password")
        result = verify_password("wrong_password", hashed_password)
        
        assert result is False
    
    def test_verify_password_empty_password(self):
        hashed_password = encode_password("some_password")
        result = verify_password("", hashed_password)
        
        assert result is False
    
    def test_verify_password_none_password(self):
        hashed_password = encode_password("some_password")
        
        with pytest.raises(ValueError):
            verify_password(None, hashed_password)
    
    def test_verify_password_invalid_hash(self):
        with pytest.raises(ValueError):
            verify_password("password", "invalid_hash")


class TestCreateToken:
    
    def test_create_token_success(self):
        payload = {"user_id": 123, "username": "testuser"}
        token = create_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_empty_payload(self):
        token = create_token({})
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_token_none_payload(self):
        with pytest.raises(ValueError):
            create_token(None)
    
    def test_create_token_with_expiry(self):
        payload = {"user_id": 123}
        expiry_hours = 24
        token = create_token(payload, expiry_hours=expiry_hours)
        
        assert token is not None


class TestValidateToken:
    
    def test_validate_token_success(self):
        payload = {"user_id": 123, "username": "testuser"}
        token = create_token(payload)
        result = validate_token(token)
        
        assert result is True
    
    def test_validate_token_invalid(self):
        result = validate_token("invalid.token.here")
        
        assert result is False
    
    def test_validate_token_expired(self):
        payload = {"user_id": 123}
        token = create_token(payload, expiry_hours=-1)
        result = validate_token(token)
        
        assert result is False
    
    def test_validate_token_empty_string(self):
        result = validate_token("")
        
        assert result is False
    
    def test_validate_token_none(self):
        with pytest.raises(ValueError):
            validate_token(None)


class TestGetTokenPayload:
    
    def test_get_token_payload_success(self):
        original_payload = {"user_id": 123, "username": "testuser", "role": "admin"}
        token = create_token(original_payload)
        extracted_payload = get_token_payload(token)
        
        assert extracted_payload is not None
        assert extracted_payload["user_id"] == original_payload["user_id"]
        assert extracted_payload["username"] == original_payload["username"]
        assert extracted_payload["role"] == original_payload["role"]
    
    def test_get_token_payload_invalid_token(self):
        with pytest.raises(ValueError):
            get_token_payload("invalid.token.here")
    
    def test_get_token_payload_expired_token(self):
        payload = {"user_id": 123}
        token = create_token(payload, expiry_hours=-1)
        with pytest.raises(ValueError):
            get_token_payload(token)
    
    def test_get_token_payload_empty_string(self):
        with pytest.raises(ValueError):
            get_token_payload("")
    
    def test_get_token_payload_none(self):
        with pytest.raises(ValueError):
            get_token_payload(None)


class TestRefreshToken:
    
    def test_refresh_token_success(self):
        original_payload = {"user_id": 123, "username": "testuser"}
        original_token = create_token(original_payload)
        new_token = refresh_token(original_token)
        
        assert new_token is not None
        assert isinstance(new_token, str)
        assert new_token != original_token
        new_payload = get_token_payload(new_token)
        
        assert new_payload["user_id"] == original_payload["user_id"]
        assert new_payload["username"] == original_payload["username"]
    
    def test_refresh_token_invalid_token(self):
        with pytest.raises(ValueError):
            refresh_token("invalid.token.here")
    
    def test_refresh_token_expired_token(self):
        payload = {"user_id": 123}
        expired_token = create_token(payload, expiry_hours=-1)
        with pytest.raises(ValueError):
            refresh_token(expired_token)
    
    def test_refresh_token_empty_string(self):
        with pytest.raises(ValueError):
            refresh_token("")


class TestRevokeToken:
    
    def test_revoke_token_success(self):
        token = create_token({"user_id": 123})
        result = revoke_token(token)
        
        assert result is True
        assert validate_token(token) is False
    
    def test_revoke_token_already_revoked(self):
        token = create_token({"user_id": 123})
        revoke_token(token)
        result = revoke_token(token)
        
        assert result is False
    
    def test_revoke_token_invalid_token(self):
        result = revoke_token("invalid.token.here")
        
        assert result is False
    
    def test_revoke_token_empty_string(self):
        result = revoke_token("")
        
        assert result is False
    
    def test_revoke_token_none(self):
        with pytest.raises(ValueError):
            revoke_token(None)


class TestAuthenticationFlow:
    
    def test_complete_auth_flow(self):
        password = "secure_password"
        hashed_password = encode_password(password)
        
        assert verify_password(password, hashed_password) is True
        
        payload = {"user_id": 123, "username": "testuser"}
        token = create_token(payload)
        
        assert validate_token(token) is True
        
        extracted_payload = get_token_payload(token)
        
        assert extracted_payload["user_id"] == payload["user_id"]
        
        new_token = refresh_token(token)
        
        assert validate_token(new_token) is True
        assert revoke_token(new_token) is True
        assert validate_token(new_token) is False
    
    def test_failed_auth_flow_wrong_password(self):
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed_password = encode_password(correct_password)
        
        assert verify_password(wrong_password, hashed_password) is False
    
    def test_failed_auth_flow_expired_token(self):
        payload = {"user_id": 123}
        expired_token = create_token(payload, expiry_hours=-1)
        
        assert validate_token(expired_token) is False
        with pytest.raises(ValueError):
            get_token_payload(expired_token)
        with pytest.raises(ValueError):
            refresh_token(expired_token)