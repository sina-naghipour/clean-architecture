import time
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
import uvicorn

START_TIME = time.time()
_is_ready = False

class HealthResponse(BaseModel):
    status: str
    uptime: float

class ReadyResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None

app = FastAPI(title="Auth Service - Health & Readiness")

async def perform_startup_checks() -> (bool, Dict[str, Any]):
    await asyncio.sleep(0)
    return True, {"note": "no checks implemented"}

@app.on_event("startup")
async def on_startup():
    global _is_ready
    try:
        ok, details = await perform_startup_checks()
        _is_ready = ok
        if not ok:
            logging.error("Startup checks failed: %s", details)
    except Exception:
        _is_ready = False
        logging.exception("Startup checks raised an exception")

@app.get("/health", response_model=HealthResponse, tags=["monitoring"])
async def health():
    return HealthResponse(status="ok", uptime=time.time() - START_TIME)

@app.get("/ready", response_model=ReadyResponse, tags=["monitoring"])
async def ready(response: Response):
    if _is_ready:
        return ReadyResponse(status="ok", details=None)
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(status="failed", details={"reason": "startup checks incomplete or failed"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)