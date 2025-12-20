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


class PasswordServiceDecorators:
    
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
