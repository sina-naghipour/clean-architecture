from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import os
from pathlib import Path

from services.file_upload_service import FileUploadService
from services.metadata_updater import MetadataUpdater
from utils.problem_details import create_problem_response


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

@router.post("/files", status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    subdirectory: str = "",
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
        return create_problem_response(
            status_code=he.status_code,
            error_type="file-upload-error",
            title="File Upload Error",
            detail=he.detail,
            instance=str(request.url)
        )

@router.post("/files/batch", status_code=207)
async def upload_files_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    subdirectory: str = "",
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
            failed.append({
                "filename": file.filename,
                "error": he.detail,
                "status_code": he.status_code
            })
    
    return {
        "successful": successful,
        "failed": failed,
        "total": len(files),
        "successful_count": len(successful)
    }

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
                title="File Not Found",
                detail="The requested file does not exist",
                instance=str(request.url)
            )
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException as he:
        return create_problem_response(
            status_code=he.status_code,
            error_type="file-error",
            title="File Error",
            detail=he.detail,
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
                title="File Not Found",
                detail="The file does not exist",
                instance=str(request.url)
            )
        
        return None
        
    except HTTPException as he:
        return create_problem_response(
            status_code=he.status_code,
            error_type="delete-error",
            title="Delete Error",
            detail=he.detail,
            instance=str(request.url)
        )

@router.get("/metadata")
async def get_metadata(
    file_service: FileUploadService = Depends(get_file_service)
):
    metadata_updater = file_service.metadata_updater
    files = metadata_updater.list_files()
    
    return {
        "files_count": len(files),
        "files": files
    }