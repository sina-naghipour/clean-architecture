from fastapi.responses import JSONResponse
from typing import Optional, Any, Dict


def create_problem_response(
    status_code: int,
    error_type: str,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    **extra_fields: Any
) -> JSONResponse:
    problem_details: Dict[str, Any] = {
        "type": f"https://example.com/errors/{error_type}",
        "title": title,
        "status": status_code,
        "detail": detail
    }
    
    if instance:
        problem_details["instance"] = instance
    
    problem_details.update(extra_fields)
    
    return JSONResponse(
        status_code=status_code,
        content=problem_details,
        media_type="application/problem+json"
    )


class ProblemDetailsException(Exception):
    def __init__(
        self,
        status_code: int,
        error_type: str,
        title: str,
        detail: str,
        instance: Optional[str] = None,
        **extra_fields: Any
    ):
        self.status_code = status_code
        self.error_type = error_type
        self.title = title
        self.detail = detail
        self.instance = instance
        self.extra_fields = extra_fields
        super().__init__(detail)
    
    def to_response(self) -> JSONResponse:
        return create_problem_response(
            status_code=self.status_code,
            error_type=self.error_type,
            title=self.title,
            detail=self.detail,
            instance=self.instance,
            **self.extra_fields
        )