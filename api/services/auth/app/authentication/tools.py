import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from decorators.auth_tools_decorators import TokenToolsDecorators, PasswordToolsDecorators, PasswordErrorHandler, TokenErrorHandler

# Environment variables with defaults
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'random-secret-key')
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv('ACCESS_TOKEN_EXPIRE_SECONDS', '280'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))

class PasswordTools:
    def __init__(self):
        pass

    @PasswordToolsDecorators.handle_encode_error
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
    def __init__(self):
        pass

    @TokenToolsDecorators.handle_creation_error
    def create_access_token(self, user_payload: dict) -> str:
        if user_payload is None:
            raise ValueError('user data cannot be None.')
        
        expiration = datetime.now() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
        token_payload = {
            **user_payload,
            'expiration': expiration.timestamp(),
            'issued_at': datetime.now().timestamp(),
            'type': 'access'
        }
        return jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256').decode('utf-8')

    @TokenToolsDecorators.handle_creation_error
    def create_refresh_token(self, user_payload: dict) -> str:
        expiration = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        token_payload = {
            **user_payload,
            'expiration': expiration.timestamp(),
            'issued_at': datetime.now().timestamp(),
            'type': 'refresh'
        }
        return jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256').decode('utf-8')

    def validate_token(self, token: str, token_type: str = "access") -> bool:
        if token is None:
            raise ValueError("Token cannot be None")
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            
            if token_type and payload.get('type') != token_type:
                return False
                
            return True
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return False
        except Exception as e:
            return TokenErrorHandler.handle_validation_error(e)

    @TokenToolsDecorators.handle_payload_error
    def get_token_payload(self, token: str) -> dict:
        if token is None:
            raise ValueError("Token cannot be None")
        
        if not token:
            raise ValueError("Token cannot be empty")
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        
        expiration_timestamp = payload.get('expiration')
        if expiration_timestamp and datetime.now().timestamp() > expiration_timestamp:
            raise ValueError("Token has expired")
        
        # clean_payload is only the user's data
        clean_payload = {
            k: v for k, v in payload.items() 
            if k not in ['expiration', 'issued_at', 'type']
        }
        return clean_payload

    @TokenToolsDecorators.handle_refresh_error
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