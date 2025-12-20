from decorators.auth_password_decorators import  PasswordServiceDecorators, PasswordErrorHandler
import bcrypt


class PasswordService:
    def __init__(self):
        pass

    @PasswordServiceDecorators.handle_encode_error
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
