# app/middlewares/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os
from dotenv import load_dotenv

load_dotenv()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        csp_policy = "default-src 'self'; "
        csp_policy += "script-src 'self' 'unsafe-inline'; "
        csp_policy += "style-src 'self' 'unsafe-inline'; "
        csp_policy += "img-src 'self' data: https:; "
        csp_policy += "connect-src 'self'; "
        csp_policy += "font-src 'self'; "
        csp_policy += "object-src 'none'; "
        csp_policy += "base-uri 'self'; "
        csp_policy += "frame-ancestors 'none'; "
        csp_policy += "form-action 'self'; "
        csp_policy += "upgrade-insecure-requests;"
        
        response.headers["Content-Security-Policy"] = csp_policy
        
        origin = request.headers.get("origin", "")
        allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
        
        if origin in allowed_origins.split(','):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if any(path in request.url.path for path in ['/orders', '/admin']):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        
        return response