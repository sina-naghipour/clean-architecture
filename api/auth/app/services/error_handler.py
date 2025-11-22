from fastapi import HTTPException
from fastapi.responses import JSONResponse
from .auth_helpers import create_problem_response

class ErrorHandler:
    def __init__(self, logger):
        self.logger = logger

    def handle_register_error(self, error: Exception, request):
        if isinstance(error, HTTPException):
            raise error
        elif isinstance(error, ValueError):
            self.logger.warning(f"Value error during registration: {str(error)}")
            return create_problem_response(
                status_code=422,
                error_type="validation",
                title="Validation failed",
                detail=str(error),
                instance=str(request.url)
            )
        else:
            self.logger.error(f"Unexpected error during registration: {str(error)}")
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail="Unexpected server error.",
                instance=str(request.url)
            )

    def handle_login_error(self, error: Exception, request):
        if isinstance(error, HTTPException):
            raise error
        elif isinstance(error, ValueError):
            self.logger.warning(f"Value error during login: {str(error)}")
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request", 
                detail=str(error),
                instance=str(request.url)
            )
        else:
            self.logger.error(f"Unexpected error during login: {str(error)}")
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail="Unexpected server error.",
                instance=str(request.url)
            )

    def handle_token_error(self, error: Exception, request):
        if isinstance(error, HTTPException):
            raise error
        elif isinstance(error, ValueError):
            self.logger.warning(f"Invalid token attempt: {str(error)}")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail=str(error),
                instance=str(request.url)
            )
        else:
            self.logger.error(f"Unexpected token error: {str(error)}")
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail="Unexpected server error.",
                instance=str(request.url)
            )

    def handle_profile_error(self, error: Exception, request):
        if isinstance(error, HTTPException):
            raise error
        elif isinstance(error, ValueError):
            self.logger.warning(f"Value error retrieving user profile: {str(error)}")
            return create_problem_response(
                status_code=401,
                error_type="unauthorized",
                title="Unauthorized",
                detail=str(error),
                instance=str(request.url)
            )
        else:
            self.logger.error(f"Unexpected error retrieving user profile: {str(error)}")
            return create_problem_response(
                status_code=500,
                error_type="internal",
                title="Internal Server Error",
                detail="Unexpected server error.",
                instance=str(request.url)
            )