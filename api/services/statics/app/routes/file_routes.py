from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import os
from pathlib import Path

from services.file_upload_service import FileUploadService
from services.metadata_updater import MetadataUpdater
from utils.problem_details import create_problem_response

DEFAULT_SUBDIRECTORY = os.getenv("DEFAULT_SUBDIRECTORY", "./general")
router = APIRouter()

def get_file_service() -> FileUploadService:
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./static/img"))
    metadata_file = Path(os.getenv("METADATA_FILE", "./metadata.json"))
    
    max_size = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))
    allowed_types = os.getenv("ALLOWED_MIME_TYPES", "image/jpeg,image/png,image/webp").split(",")
    
    metadata_updater = MetadataUpdater(metadata_file)
    
    return FileUploadService(
        upload_dir=upload_dir,
        metadata_updater=metadata_updater,
        max_file_size=max_size,
        allowed_mime_types=allowed_types
    )


def _map_status_to_error(status_code: int) -> tuple[str, str]:
    mapping = {
        400: ("bad-request", "Bad Request"),
        401: ("unauthorized", "Unauthorized"),
        403: ("forbidden", "Forbidden"),
        404: ("not-found", "Not Found"),
        409: ("conflict", "Conflict"),
        413: ("file-too-large", "File Too Large"),
        415: ("unsupported-media-type", "Unsupported Media Type"),
        422: ("validation", "Validation Failed"),
        500: ("internal", "Internal Server Error"),
    }
    return mapping.get(status_code, ("internal", "Internal Server Error"))


@router.post("/files", status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    subdirectory: str = DEFAULT_SUBDIRECTORY,
    file_service: FileUploadService = Depends(get_file_service)
):
    try:
        result = await file_service.upload_file(
            upload_file=file,
            subdirectory=subdirectory
        )
        
        response = JSONResponse(
            status_code=201,
            content=result,
            headers={"Location": f"/api/files/{result['id']}"}
        )
        return response
        
    except HTTPException as he:
        error_type, title = _map_status_to_error(he.status_code)
        return create_problem_response(
            status_code=he.status_code,
            error_type=error_type,
            title=title,
            detail=he.detail,
            instance=str(request.url)
        )
    except Exception as e:
        return create_problem_response(
            status_code=500,
            error_type="internal",
            title="Internal Server Error",
            detail=f"An unexpected error occurred: {str(e)}",
            instance=str(request.url)
        )


@router.post("/files/batch", status_code=207)
async def upload_files_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    subdirectory: str = DEFAULT_SUBDIRECTORY,
    file_service: FileUploadService = Depends(get_file_service)
):
    successful = []
    failed = []
    
    for file in files:
        try:
            result = await file_service.upload_file(
                upload_file=file,
                subdirectory=subdirectory
            )
            successful.append(result)
        except HTTPException as he:
            error_type, title = _map_status_to_error(he.status_code)
            failed.append({
                "filename": file.filename,
                "error": he.detail,
                "status_code": he.status_code,
                "error_type": error_type,
                "title": title
            })
        except Exception as e:
            failed.append({
                "filename": file.filename,
                "error": f"Unexpected error: {str(e)}",
                "status_code": 500,
                "error_type": "internal",
                "title": "Internal Server Error"
            })
    
    # Return multi-status response following catalog format
    multi_status_response = {
        "type": "https://example.com/errors/multi-status",
        "title": "Multi-Status",
        "status": 207,
        "detail": "Batch operation completed with partial success",
        "instance": str(request.url),
        "successful_count": len(successful),
        "failed_count": len(failed),
        "successful": successful,
        "failed": failed
    }
    
    return JSONResponse(
        status_code=207,
        content=multi_status_response,
        media_type="application/problem+json"
    )


@router.get("/files/{file_id}")
async def get_file(
    request: Request,
    file_id: str,
    file_service: FileUploadService = Depends(get_file_service)
):
    try:
        file_path = file_service.get_file_path(file_id)
        
        if not file_path.exists():
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="The requested file does not exist",
                instance=str(request.url)
            )
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException as he:
        error_type, title = _map_status_to_error(he.status_code)
        return create_problem_response(
            status_code=he.status_code,
            error_type=error_type,
            title=title,
            detail=he.detail,
            instance=str(request.url)
        )
    except Exception as e:
        return create_problem_response(
            status_code=500,
            error_type="internal",
            title="Internal Server Error",
            detail=f"An unexpected error occurred: {str(e)}",
            instance=str(request.url)
        )


@router.delete("/files/{file_id}", status_code=204)
async def delete_file(
    request: Request,
    file_id: str,
    file_service: FileUploadService = Depends(get_file_service)
):
    try:
        deleted = await file_service.delete_file(file_id)
        
        if not deleted:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="The file does not exist",
                instance=str(request.url)
            )
        
        return None
        
    except HTTPException as he:
        error_type, title = _map_status_to_error(he.status_code)
        return create_problem_response(
            status_code=he.status_code,
            error_type=error_type,
            title=title,
            detail=he.detail,
            instance=str(request.url)
        )
    except Exception as e:
        return create_problem_response(
            status_code=500,
            error_type="internal",
            title="Internal Server Error",
            detail=f"An unexpected error occurred: {str(e)}",
            instance=str(request.url)
        )


@router.get("/metadata")
async def get_metadata(
    request: Request,
    file_service: FileUploadService = Depends(get_file_service)
):
    try:
        metadata_updater = file_service.metadata_updater
        files = metadata_updater.list_files()
        
        return {
            "files_count": len(files),
            "files": files
        }
        
    except Exception as e:
        return create_problem_response(
            status_code=500,
            error_type="internal",
            title="Internal Server Error",
            detail=f"An unexpected error occurred: {str(e)}",
            instance=str(request.url) if request else ""
        )