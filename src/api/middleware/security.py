"""
Security headers middleware.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers de segurança em todas as respostas.
    
    Headers implementados:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000 (apenas HTTPS)
    - Content-Security-Policy: Configurado para permitir Swagger UI
    """
    
    # CDNs permitidos para Swagger UI
    SWAGGER_CDN = "https://cdn.jsdelivr.net"
    FASTAPI_CDN = "https://fastapi.tiangolo.com"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Processa requisição e adiciona headers de segurança."""
        response = await call_next(request)
        
        settings = get_settings()
        
        # Headers básicos (sempre)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS apenas em produção e HTTPS
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP configurado para permitir Swagger UI
        # - script-src: CDN do Swagger + inline para funcionamento
        # - style-src: CDN do Swagger + inline para estilos
        # - img-src: FastAPI favicon + data URIs do Swagger
        # - font-src: CDN para fontes do Swagger
        csp_parts = [
            "default-src 'self'",
            f"script-src 'self' 'unsafe-inline' {self.SWAGGER_CDN}",
            f"style-src 'self' 'unsafe-inline' {self.SWAGGER_CDN}",
            f"img-src 'self' data: {self.FASTAPI_CDN}",
            f"font-src 'self' {self.SWAGGER_CDN}",
            "connect-src 'self'",
        ]
        csp = "; ".join(csp_parts)
        response.headers["Content-Security-Policy"] = csp
        
        return response
