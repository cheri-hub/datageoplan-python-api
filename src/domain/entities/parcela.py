"""
Entidade Parcela - representa uma parcela no SIGEF.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ParcelaSituacao(str, Enum):
    """Situação da parcela no SIGEF."""
    
    CERTIFICADA = "certificada"
    PENDENTE = "pendente"
    CANCELADA = "cancelada"
    EM_ANALISE = "em_analise"


class TipoExportacao(str, Enum):
    """Tipos de exportação disponíveis no SIGEF."""
    
    PARCELA = "parcela"
    VERTICE = "vertice"
    LIMITE = "limite"


@dataclass
class Coordenada:
    """Representa uma coordenada geográfica."""
    
    latitude: float
    longitude: float
    altitude: float | None = None
    
    def to_tuple(self) -> tuple[float, float]:
        """Retorna como tupla (lat, lon)."""
        return (self.latitude, self.longitude)


@dataclass
class Vertice:
    """Representa um vértice de uma parcela."""
    
    codigo: str
    coordenada: Coordenada
    tipo: str = "M"  # M = Marco, V = Vértice virtual
    sigma_x: float | None = None
    sigma_y: float | None = None
    sigma_z: float | None = None


@dataclass
class Limite:
    """Representa um limite/confrontação de uma parcela."""
    
    codigo: str
    tipo: str  # Natural, Artificial, etc.
    vertice_inicial: str
    vertice_final: str
    azimute: float | None = None
    distancia: float | None = None
    confrontante: str | None = None


@dataclass
class Parcela:
    """
    Representa uma parcela georreferenciada no SIGEF.
    
    A parcela é a unidade fundamental do SIGEF INCRA,
    representando um imóvel rural certificado.
    """
    
    # Identificação
    codigo: str  # Código SIGEF (ex: "a1b2c3d4-...")
    
    # Dados básicos
    denominacao: str | None = None
    area_ha: float | None = None
    perimetro_m: float | None = None
    municipio: str | None = None
    uf: str | None = None
    
    # Status
    situacao: ParcelaSituacao = ParcelaSituacao.PENDENTE
    data_certificacao: datetime | None = None
    codigo_ccir: str | None = None
    
    # Dados geométricos
    vertices: list[Vertice] = field(default_factory=list)
    limites: list[Limite] = field(default_factory=list)
    centroide: Coordenada | None = None
    
    # Proprietários
    proprietarios: list[dict[str, Any]] = field(default_factory=list)
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    
    def __post_init__(self):
        """Validação após inicialização."""
        self.codigo = self.codigo.strip().lower()
    
    def is_certificada(self) -> bool:
        """Verifica se a parcela está certificada."""
        return self.situacao == ParcelaSituacao.CERTIFICADA
    
    def get_url_sigef(self) -> str:
        """Retorna URL da parcela no SIGEF."""
        return f"https://sigef.incra.gov.br/geo/parcela/detalhe/{self.codigo}/"
    
    def get_download_urls(self) -> dict[TipoExportacao, str]:
        """Retorna URLs de download dos CSVs."""
        base = "https://sigef.incra.gov.br/geo/exportar"
        return {
            TipoExportacao.PARCELA: f"{base}/parcela/csv/{self.codigo}/",
            TipoExportacao.VERTICE: f"{base}/vertice/csv/{self.codigo}/",
            TipoExportacao.LIMITE: f"{base}/limite/csv/{self.codigo}/",
        }
