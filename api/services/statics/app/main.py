from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
import os
from pathlib import Path
import json

from routes.file_routes import router as file_router
from utils.problem_details import create_problem_response


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./static/img"))
    metadata_file = Path(os.getenv("METADATA_FILE", "./metadata.json"))
    
    upload_dir.mkdir(parents=True, exist_ok=True)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not metadata_file.exists():
        with open(metadata_file, 'w') as f:
            json.dump({}, f)
            
    logger.info(f"Static service starting...")
    logger.info(f"Upload directory: {upload_dir}")
    logger.info(f"Metadata file: {metadata_file}")
    
    yield
    
    logger.info("Static service shutting down...")

app = FastAPI(
    title="Static File Service",
    description="Secure file storage service with magic-number validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler: {str(exc)}", exc_info=True)
    return create_problem_response(
        status_code=500,
        error_type="internal-server-error",
        title="Internal Server Error",
        detail="An unexpected error occurred",
        instance=str(request.url)
    )

@app.get("/health")
async def health_check():
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./static/img"))
    metadata_file = Path(os.getenv("METADATA_FILE", "./metadata.json"))
    
    checks = {
        "upload_dir_exists": upload_dir.exists(),
        "upload_dir_writable": os.access(upload_dir, os.W_OK),
        "metadata_file_exists": metadata_file.exists() or metadata_file.parent.exists(),
        "service": "static",
        "status": "healthy"
    }
    
    all_healthy = all(checks.values())
    
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content=checks
    )

@app.get("/")
async def root():
    return {
        "service": "static-file-service",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /files",
            "batch_upload": "POST /files/batch",
            "download": "GET /files/{file_id}",
            "delete": "DELETE /files/{file_id}",
            "metadata": "GET /metadata",
            "health": "GET /health",
            "docs": "/docs"
        }
    }

app.include_router(file_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8002")),
        reload=os.getenv("RELOAD", "True").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info")
    )