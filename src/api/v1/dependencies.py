"""
Injeção de Dependências.

Configura e fornece instâncias dos serviços
usando o sistema de dependency injection do FastAPI.
"""

import secrets
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import Settings, get_settings
from src.core.logging import get_logger
from src.domain.interfaces import IGovBrAuthenticator, ISessionRepository, ISigefClient
from src.infrastructure.govbr import PlaywrightGovBrAuthenticator
from src.infrastructure.persistence import FileSessionRepository
from src.infrastructure.sigef import HttpSigefClient
from src.services.auth_service import AuthService
from src.services.sigef_service import SigefService

logger = get_logger(__name__)


# ============== Segurança ==============

# Esquemas de autenticação
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Annotated[str | None, Security(api_key_header)] = None,
) -> str:
    """
    Valida API Key via header X-API-Key.
    
    Header: X-API-Key: sua-api-key
    
    Raises:
        HTTPException: Se API Key inválida ou ausente
    
    Returns:
        API Key validada
    """
    settings = get_settings()
    
    # Em desenvolvimento, permite sem API Key
    if settings.is_development:
        return "dev-mode"
    
    if not api_key:
        logger.warning("Requisição sem API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key não fornecida. Use header 'X-API-Key'",
        )
    
    # Valida API Key (constant-time comparison previne timing attacks)
    if not secrets.compare_digest(api_key, settings.api_key):
        logger.warning("API Key inválida fornecida")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida",
        )
    
    return api_key


# Type alias para uso nos endpoints
RequireAPIKey = Annotated[str, Depends(verify_api_key)]


# ============== Infraestrutura ==============

@lru_cache
def get_session_repository() -> ISessionRepository:
    """Retorna repositório de sessões (singleton)."""
    return FileSessionRepository()


@lru_cache
def get_govbr_authenticator() -> IGovBrAuthenticator:
    """Retorna autenticador Gov.br (singleton)."""
    return PlaywrightGovBrAuthenticator()


@lru_cache
def get_sigef_client() -> ISigefClient:
    """Retorna cliente SIGEF (singleton)."""
    return HttpSigefClient()


# ============== Serviços ==============

@lru_cache
def get_auth_service() -> AuthService:
    """Retorna serviço de autenticação (singleton)."""
    return AuthService(
        govbr_authenticator=get_govbr_authenticator(),
        sigef_client=get_sigef_client(),
        session_repository=get_session_repository(),
    )


@lru_cache
def get_sigef_service() -> SigefService:
    """Retorna serviço SIGEF (singleton)."""
    return SigefService(
        sigef_client=get_sigef_client(),
        session_repository=get_session_repository(),
        auth_service=get_auth_service(),
    )


# ============== CAR BBox ==============

@lru_cache
def get_car_wfs_client() -> "CarWfsClient":
    """Retorna cliente WFS do GeoServer SICAR (singleton)."""
    from src.infrastructure.car_wfs import CarWfsClient
    return CarWfsClient()


@lru_cache
def get_car_bbox_service() -> "CarBboxService":
    """Retorna serviço de consulta CAR por BBox (singleton)."""
    from src.services.car_bbox_service import CarBboxService
    return CarBboxService(wfs_client=get_car_wfs_client())


# ============== INCRA BBox (GeoOne) ==============

@lru_cache
def get_geoone_wfs_client() -> "GeoOneWfsClient":
    """Retorna cliente WFS do GeoOne GeoINCRA (singleton)."""
    from src.infrastructure.geoone_wfs import GeoOneWfsClient
    return GeoOneWfsClient()


@lru_cache
def get_incra_bbox_service() -> "IncraBboxService":
    """Retorna serviço de consulta INCRA por BBox (singleton)."""
    from src.services.incra_bbox_service import IncraBboxService
    return IncraBboxService(wfs_client=get_geoone_wfs_client())


# ============== Reset (para testes) ==============

def reset_dependencies() -> None:
    """Limpa cache de dependências (útil para testes)."""
    get_session_repository.cache_clear()
    get_govbr_authenticator.cache_clear()
    get_sigef_client.cache_clear()
    get_auth_service.cache_clear()
    get_sigef_service.cache_clear()
    get_car_wfs_client.cache_clear()
    get_car_bbox_service.cache_clear()
    get_geoone_wfs_client.cache_clear()
    get_incra_bbox_service.cache_clear()
