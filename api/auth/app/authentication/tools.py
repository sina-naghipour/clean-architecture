import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps

class PasswordErrorHandler:
    @staticmethod
    def handle_encode_error(error: Exception) -> str:
        if isinstance(error, ValueError):
            raise error
        raise ValueError("Failed to encode password") from error

    @staticmethod
    def handle_verify_error(error: Exception) -> bool:
        if isinstance(error, ValueError):
            raise error
        raise ValueError("Failed to verify password") from error

class TokenErrorHandler:
    @staticmethod
    def handle_creation_error(error: Exception) -> str:
        if isinstance(error, ValueError):
            raise error
        raise ValueError("Failed to create token") from error

    @staticmethod
    def handle_validation_error(error: Exception) -> bool:
        if isinstance(error, ValueError):
            raise error
        return False

    @staticmethod
    def handle_payload_error(error: Exception) -> dict:
        if isinstance(error, ValueError):
            raise error
        raise ValueError("Failed to get token payload") from error

    @staticmethod
    def handle_refresh_error(error: Exception) -> str:
        if isinstance(error, ValueError):
            raise error
        raise ValueError("Failed to refresh token") from error

def handle_password_encode_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            PasswordErrorHandler.handle_encode_error(e)
    return wrapper

def handle_password_verify_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            PasswordErrorHandler.handle_verify_error(e)
    return wrapper

def handle_token_creation_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            TokenErrorHandler.handle_creation_error(e)
    return wrapper

def handle_token_payload_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            TokenErrorHandler.handle_payload_error(e)
    return wrapper

def handle_token_refresh_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            TokenErrorHandler.handle_refresh_error(e)
    return wrapper

class PasswordTools:
    def __init__(self):
        pass

    @handle_password_encode_error
    def encode_password(self, plain_password: str) -> str:
        if plain_password is None:
            raise ValueError('password cannot be None.')
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')
        return hashed

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if plain_password is None:
            raise ValueError('password cannot be None.')
       
        if not hashed_password or not isinstance(hashed_password, str):
            raise ValueError("Invalid hashed password")
        
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except (ValueError, TypeError) as e:
            raise ValueError('Invalid hashed password format')
        except Exception as e:
            PasswordErrorHandler.handle_verify_error(e)

class TokenTools:

    @handle_token_creation_error
    def create_access_token(self, user_payload: dict) -> str:
        if user_payload is None:
            raise ValueError('user data cannot be None.')
        
        expiration = datetime.now() + timedelta(seconds=280)
        token_payload = {
            **user_payload,
            'expiration': expiration.timestamp(),
            'issued_at': datetime.now().timestamp(),
            'type': 'access'
        }
        return jwt.encode(token_payload, 'random-secret-key', algorithm='HS256')

    @handle_token_creation_error
    def create_refresh_token(self, user_payload: dict) -> str:
        expiration = datetime.utcnow() + timedelta(days=7)
        token_payload = {
            **user_payload,
            'expiration': expiration.timestamp(),
            'issued_at': datetime.now().timestamp(),
            'type': 'refresh'
        }
        return jwt.encode(token_payload, 'random-secret-key', algorithm='HS256')

    def validate_token(self, token: str, token_type: str = "access") -> bool:
        if token is None:
            raise ValueError("Token cannot be None")
        
        try:
            payload = jwt.decode(token, 'random-secret-key', algorithms=['HS256'])
            
            if token_type and payload.get('type') != token_type:
                return False
                
            return True
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return False
        except Exception as e:
            return TokenErrorHandler.handle_validation_error(e)

    @handle_token_payload_error
    def get_token_payload(self, token: str) -> dict:
        if token is None:
            raise ValueError("Token cannot be None")
        
        if not token:
            raise ValueError("Token cannot be empty")
        
        payload = jwt.decode(token, 'random-secret-key', algorithms=['HS256'])
        
        expiration_timestamp = payload.get('expiration')
        if expiration_timestamp and datetime.now().timestamp() > expiration_timestamp:
            raise ValueError("Token has expired")
        
        # clean_payload is only the user's data
        clean_payload = {
            k: v for k, v in payload.items() 
            if k not in ['expiration', 'issued_at', 'type']
        }
        return clean_payload

    @handle_token_refresh_error
    def refresh_access_token(self, refresh_token: str) -> str:
        if not refresh_token:
            raise ValueError("Refresh token cannot be empty")
        
        if not self.validate_token(refresh_token, "refresh"):
            raise ValueError("Invalid or expired refresh token")
        
        payload = self.get_token_payload(refresh_token)
        user_id = payload.get('user_id')
        
        if not user_id:
            raise ValueError("Invalid refresh token payload")
        
        user_data = {'user_id': user_id}
        
        new_access_token = self.create_access_token(user_data)
        
        return new_access_token