"""
Rotas v1 da API - Versão Mínima.
"""

from fastapi import APIRouter

from src.api.v1.routes.auth import router as auth_router
from src.api.v1.routes.sigef import router as sigef_router
from src.api.v1.routes.sicar import router as sicar_router

router = APIRouter()

# Inclui rotas
router.include_router(auth_router)
router.include_router(sigef_router)
router.include_router(sicar_router)


@router.get("/", tags=["Info"])
async def api_info():
    """Informações da API."""
    return {
        "version": "1.0.0",
        "description": "API para integração com sistemas de dados geoespaciais",
        "platforms": {
            "sigef": {
                "name": "SIGEF - Sistema de Gestão Fundiária",
                "status": "active",
                "endpoints": "/api/sigef",
            },
            "sicar": {
                "name": "SICAR - Sistema de Cadastro Ambiental Rural",
                "status": "active",
                "endpoints": "/api/sicar",
            },
        },
        "auth": "/api/auth",
    }
