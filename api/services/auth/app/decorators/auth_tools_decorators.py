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


class PasswordToolsDecorators:
    
    @staticmethod
    def handle_encode_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                PasswordErrorHandler.handle_encode_error(e)
        return wrapper

    @staticmethod
    def handle_verify_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                PasswordErrorHandler.handle_verify_error(e)
        return wrapper

class TokenToolsDecorators:
    
    @staticmethod
    def handle_creation_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                TokenErrorHandler.handle_creation_error(e)
        return wrapper

    @staticmethod
    def handle_payload_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                TokenErrorHandler.handle_payload_error(e)
        return wrapper

    @staticmethod
    def handle_refresh_error(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                TokenErrorHandler.handle_refresh_error(e)
        return wrapper