"""
Injeção de Dependências.

Configura e fornece instâncias dos serviços
usando o sistema de dependency injection do FastAPI.
"""

from functools import lru_cache

from src.core.config import Settings, get_settings
from src.domain.interfaces import IGovBrAuthenticator, ISessionRepository, ISigefClient
from src.infrastructure.govbr import PlaywrightGovBrAuthenticator
from src.infrastructure.persistence import FileSessionRepository
from src.infrastructure.sigef import HttpSigefClient
from src.services.auth_service import AuthService
from src.services.sigef_service import SigefService


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


# ============== Reset (para testes) ==============

def reset_dependencies() -> None:
    """Limpa cache de dependências (útil para testes)."""
    get_session_repository.cache_clear()
    get_govbr_authenticator.cache_clear()
    get_sigef_client.cache_clear()
    get_auth_service.cache_clear()
    get_sigef_service.cache_clear()
