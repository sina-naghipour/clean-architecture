from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from middlewares.auth_middleware import AuthMiddleware
from database.connection import db_connection, init_db, health_check_db

load_dotenv()

from routes.order_routes import router as order_router

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8003'))
RELOAD = os.getenv('RELOAD', 'True').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
LOG_FILE = os.getenv('LOG_FILE', 'order_service.log')

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
    logger.info("Starting Order Service...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Host: {HOST}, Port: {PORT}")
    
    try:
        await init_db()
        logger.info("Database connection pool initialized")
        
        pool_config = {
            "pool_size": os.getenv("DB_POOL_SIZE", "20"),
            "max_overflow": os.getenv("DB_MAX_OVERFLOW", "10"),
            "pool_timeout": os.getenv("DB_POOL_TIMEOUT", "30"),
            "pool_recycle": os.getenv("DB_POOL_RECYCLE", "3600"),
        }
        logger.info(f"Database pool configuration: {pool_config}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    await db_connection.close()
    logger.info("Database connection pool closed")
    
    logger.info("Shutting down Order Service...")

app = FastAPI(
    title="Ecommerce API - Order Service",
    description="Order management microservice for Ecommerce API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
    )
)
trace.set_tracer_provider(tracer_provider)

FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)


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

@app.get("/routes", tags=["Debug"])
async def list_all_routes(request: Request):
    routes = []
    for route in request.app.routes:
        route_info = {
            "path": route.path,
            "methods": list(route.methods) if hasattr(route, 'methods') else [],
            "name": route.name if hasattr(route, 'name') else None,
            "endpoint": str(route.endpoint) if hasattr(route, 'endpoint') else None
        }
        routes.append(route_info)
    
    return {
        "service": "authentication",
        "total_routes": len(routes),
        "routes": routes
    }

@app.get("/health", tags=["Health"])
async def health_check():
    db_health = await health_check_db()
    
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "service": "order",
        "timestamp": "2024-01-01T00:00:00Z",
        "environment": ENVIRONMENT,
        "database": db_health
    }

@app.get("/ready", tags=["Health"])
async def readiness_check():
    try:
        from sqlalchemy import text
        async with db_connection.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            
        pool_stats = await db_connection.get_pool_stats()
        
        return {
            "status": "ready",
            "service": "order",
            "timestamp": "2024-01-01T00:00:00Z",
            "database": {
                "status": "ready",
                "pool_stats": pool_stats
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "order",
            "timestamp": "2024-01-01T00:00:00Z",
            "error": f"Database not ready: {str(e)}"
        }

@app.get("/info", tags=["Root"])
async def root():
    return {
        "message": "Ecommerce Order Service",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }

@app.get("/debug/pool", tags=["Debug"])
async def debug_pool():
    try:
        pool_stats = await db_connection.get_pool_stats()
        return {
            "database": {
                "pool_config": {
                    "pool_size": os.getenv("DB_POOL_SIZE", "20"),
                    "max_overflow": os.getenv("DB_MAX_OVERFLOW", "10"),
                    "pool_timeout": os.getenv("DB_POOL_TIMEOUT", "30"),
                    "pool_recycle": os.getenv("DB_POOL_RECYCLE", "3600"),
                },
                "pool_stats": pool_stats
            }
        }
    except Exception as e:
        return {"error": str(e)}

app.include_router(order_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level=LOG_LEVEL
    )