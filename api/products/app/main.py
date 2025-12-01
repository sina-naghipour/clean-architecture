from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from routes.product_routes import router as product_router

# Environment variables with defaults
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8001'))
RELOAD = os.getenv('RELOAD', 'True').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
LOG_FILE = os.getenv('LOG_FILE', 'product_service.log')

ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(',')]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Product Service...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Host: {HOST}, Port: {PORT}")
    
    yield
    
    logger.info("Shutting down Product Service...")

app = FastAPI(
    title="Ecommerce API - Product Service",
    description="Product catalog microservice for Ecommerce API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://example.com/errors/internal",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url)
        },
        media_type="application/problem+json"
    )

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "product",
        "timestamp": "2024-01-01T00:00:00Z",
        "environment": ENVIRONMENT
    }

@app.get("/info", tags=["Root"])
async def root():
    return {
        "message": "Ecommerce Product Service",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }

app.include_router(product_router)
app.include_router(image_router)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level=LOG_LEVEL
    )