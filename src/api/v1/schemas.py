"""
Schemas Pydantic para validação de requests/responses da API.
Versão mínima para cliente C#.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TipoExportacaoEnum(str, Enum):
    """Tipos de exportação disponíveis."""
    
    PARCELA = "parcela"
    VERTICE = "vertice"
    LIMITE = "limite"


# ============== Auth Schemas ==============

class SessionInfoResponse(BaseModel):
    """Informações da sessão atual."""
    
    session_id: str
    cpf: str | None
    nome: str | None
    is_valid: bool
    is_govbr_authenticated: bool
    is_sigef_authenticated: bool
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None


class AuthStatusResponse(BaseModel):
    """Status de autenticação."""
    
    authenticated: bool
    session: SessionInfoResponse | None = None
    message: str


class BrowserLoginResponse(BaseModel):
    """Resposta de login via navegador do cliente."""
    
    auth_token: str
    session_id: str
    login_url: str


class BrowserCallbackRequest(BaseModel):
    """Request para retornar dados da autenticação via navegador."""
    
    auth_token: str
    govbr_cookies: list[dict]
    sigef_cookies: list[dict] | None = None
    jwt_payload: dict | None = None


# ============== Health Schemas ==============

class HealthResponse(BaseModel):
    """Resposta de health check."""
    
    status: str
    version: str
    environment: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Resposta de erro padrão."""
    
    error: str
    detail: str | None = None
    code: str | None = None
