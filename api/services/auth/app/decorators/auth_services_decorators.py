from functools import wraps
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from services.auth_helpers import create_problem_response

def handle_database_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            self = args[0]
            request = next((arg for arg in args if hasattr(arg, 'url')), None)
            
            self.logger.error(f"Database integrity error in {func.__name__}: {e}")
            return create_problem_response(
                status_code=409,
                error_type="conflict",
                title="Conflict",
                detail="Resource conflict occurred",
                instance=str(request.url) if request else ""
            )
        except SQLAlchemyError as e:
            self = args[0]
            request = next((arg for arg in args if hasattr(arg, 'url')), None)
            
            self.logger.error(f"Database error in {func.__name__}: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal_error",
                title="Internal Server Error",
                detail="Database operation failed",
                instance=str(request.url) if request else ""
            )
    return wrapper

def handle_validation_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            self = args[0]
            request = next((arg for arg in args if hasattr(arg, 'url')), None)
            
            self.logger.warning(f"Validation error in {func.__name__}: {e}")
            return create_problem_response(
                status_code=400,
                error_type="bad_request",
                title="Bad Request",
                detail=str(e),
                instance=str(request.url) if request else ""
            )
    return wrapper

def handle_unexpected_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self = args[0]
            request = next((arg for arg in args if hasattr(arg, 'url')), None)
            
            self.logger.error(f"Unexpected error in {func.__name__}: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal_error",
                title="Internal Server Error",
                detail="An unexpected error occurred",
                instance=str(request.url) if request else ""
            )
    return wrapper

def handle_repository_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper