"""
Schemas Pydantic para validação de requests/responses da API.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


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


class LoginResponse(BaseModel):
    """Resposta de login."""
    
    success: bool
    message: str
    session: SessionInfoResponse | None = None


# ============== SIGEF Schemas ==============

class ParcelaInfoResponse(BaseModel):
    """Informações de uma parcela."""
    
    codigo: str
    denominacao: str | None = None
    area_ha: float | None = None
    perimetro_m: float | None = None
    municipio: str | None = None
    uf: str | None = None
    situacao: str
    url: str


class DownloadRequest(BaseModel):
    """Request para download de CSV."""
    
    codigo: str = Field(
        ...,
        description="Código SIGEF da parcela (UUID)",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    tipo: TipoExportacaoEnum = Field(
        ...,
        description="Tipo de exportação",
    )
    
    @field_validator("codigo")
    @classmethod
    def validate_codigo(cls, v: str) -> str:
        """Valida formato do código."""
        import re
        
        v = v.strip().lower()
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        
        if not re.match(pattern, v):
            raise ValueError("Código de parcela inválido. Deve ser um UUID.")
        
        return v


class DownloadAllRequest(BaseModel):
    """Request para download de todos os CSVs."""
    
    codigo: str = Field(
        ...,
        description="Código SIGEF da parcela (UUID)",
    )
    
    @field_validator("codigo")
    @classmethod
    def validate_codigo(cls, v: str) -> str:
        """Valida formato do código."""
        import re
        
        v = v.strip().lower()
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        
        if not re.match(pattern, v):
            raise ValueError("Código de parcela inválido. Deve ser um UUID.")
        
        return v


class BatchDownloadRequest(BaseModel):
    """Request para download em lote."""
    
    codigos: list[str] = Field(
        ...,
        description="Lista de códigos SIGEF",
        min_length=1,
        max_length=100,
    )
    tipos: list[TipoExportacaoEnum] | None = Field(
        default=None,
        description="Tipos a baixar (default: todos)",
    )


class DownloadResponse(BaseModel):
    """Resposta de download."""
    
    success: bool
    message: str
    arquivo: str | None = None
    tamanho_bytes: int | None = None


class DownloadAllResponse(BaseModel):
    """Resposta de download de todos os CSVs."""
    
    success: bool
    message: str
    arquivos: dict[str, str] = Field(
        default_factory=dict,
        description="Mapeamento tipo -> caminho do arquivo",
    )


class BatchDownloadResponse(BaseModel):
    """Resposta de download em lote."""
    
    success: bool
    message: str
    total: int
    sucesso: int
    falhas: int
    resultados: dict[str, dict[str, str]]


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
