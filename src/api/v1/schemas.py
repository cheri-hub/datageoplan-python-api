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


# ============== SICAR/CAR Schemas ==============

class TemaCAR(BaseModel):
    """Informações de um tema CAR."""
    
    tema_car: str
    arquivo_modelo: str
    cor_preenchimento: str | None
    cor_contorno: str
    tipo: str  # "Polygon" ou "Point"


class GrupoCAR(BaseModel):
    """Informações de um grupo de temas CAR."""
    
    classe: str
    nome_grupo: str
    ordem: int
    num_temas: int


class GrupoTemasCAR(BaseModel):
    """Grupo com lista de temas."""
    
    classe: str
    nome_grupo: str
    ordem: int
    temas: list[TemaCAR]


class ResultadoProcessamentoCAR(BaseModel):
    """Resultado do processamento de CAR."""
    
    sucesso: bool
    recibo: str | None
    temas_processados: int
    feicoes_total: int
    arquivos_gerados: list[str]
    erros: list[str] | None = None


class ProcessedStateRequest(BaseModel):
    """Request para download processado por estado."""
    
    state: str
    polygon: str
    include_sld: bool = True
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "state": "SP",
                "polygon": "AREA_PROPERTY",
                "include_sld": True
            }
        }
    }


class ProcessedCARRequest(BaseModel):
    """Request para download processado por número CAR."""
    
    car_number: str
    include_sld: bool = True
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "car_number": "SP-3538709-4861E981046E49BC81720C879459E554",
                "include_sld": True
            }
        }
    }


class PaletaCoresResponse(BaseModel):
    """Resposta com paleta de cores dos temas."""
    
    arquivo_modelo: str
    tema_car: str
    cor_preenchimento: str | None
    cor_contorno: str
    tipo: str
