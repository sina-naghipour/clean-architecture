from fastapi.responses import JSONResponse

def create_problem_response(
    status_code: int,
    error_type: str,
    title: str,
    detail: str,
    instance: str
) -> JSONResponse:
    problem_details = {
        "type": f"https://example.com/errors/{error_type}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance
    }
    return JSONResponse(
        status_code=status_code,
        content=problem_details,
        media_type="application/problem+json"
    )