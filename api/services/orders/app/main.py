from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import HTTPException
from sqlalchemy import text

import os
from dotenv import load_dotenv

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from middlewares.auth_middleware import AuthMiddleware
from database.connection import db_connection

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
        await db_connection.connect()
        logger.info("Database connection pool initialized")
        
        pool_config = {
            'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '1800')),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
        }
        logger.info(f"Database pool configuration: {pool_config}")
        
        if ENVIRONMENT == 'development':
            await db_connection.create_tables()
            logger.info("Database tables created/verified")
            
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Order Service...")
    
    try:
        await db_connection.close()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}")

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
    return {
        "status": "healthy",
        "service": "order",
        "timestamp": "2024-01-01T00:00:00Z",
        "environment": ENVIRONMENT
    }

@app.get("/health/db", tags=["Health"])
async def db_health():
    import time
    try:
        async with db_connection.engine.connect() as conn:
            start = time.time()
            await conn.execute(text("SELECT 1"))
            latency = time.time() - start
            
            pool = db_connection.engine.pool
            return {
                "status": "healthy",
                "latency_ms": round(latency * 1000, 2),
                "pool": {
                    "size": pool.size(),
                    "connections_in_use": pool.checkedout(),
                    "connections_idle": pool.checkedin(),
                    "overflow": pool.overflow(),
                }
            }
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        raise HTTPException(503, detail="Database unhealthy")

@app.get("/ready", tags=["Health"])
async def readiness_check():
    try:
        await db_connection.get_session()
        return {
            "status": "ready",
            "service": "order",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "order",
                "error": "Database unavailable"
            }
        )

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

@app.get("/health/db-pool", tags=["Health", "Monitoring"])
async def db_pool_health():
    try:
        engine = db_connection.engine
        
        if not engine:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "Database engine not initialized"
                }
            )
        
        pool = engine.pool
        stats = {
            "status": "healthy",
            "pool_size": getattr(pool, '_max_overflow', 'unknown'),
            "checked_in": getattr(pool, 'checkedin', lambda: 'unknown')(),
            "checked_out": getattr(pool, 'checkedout', lambda: 'unknown')(),
            "pool_overflow": getattr(pool, 'overflow', lambda: 'unknown')(),
            "pool_timeout": getattr(pool, 'timeout', 'unknown'),
        }
        
        return stats
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

app.include_router(order_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level=LOG_LEVEL
    )