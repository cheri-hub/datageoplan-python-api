"""
Entidades do domínio.
"""

from src.domain.entities.parcela import (
    Coordenada,
    Limite,
    Parcela,
    ParcelaSituacao,
    TipoExportacao,
    Vertice,
)
from src.domain.entities.session import Cookie, JWTPayload, Session
from src.domain.entities.car_bbox import (
    StatusImovelSicar,
    TipoImovelSicar,
    UfSicar,
    UF_BBOXES,
    detectar_ufs_por_bbox,
)
from src.domain.entities.incra_wfs import (
    CamadaIncra,
    StatusCertificacao,
    CAMADA_LAYER_MAP,
    CAMADA_DESCRICAO,
    UF_ID_PARA_SIGLA,
)

__all__ = [
    # Session
    "Session",
    "Cookie",
    "JWTPayload",
    # Parcela
    "Parcela",
    "ParcelaSituacao",
    "TipoExportacao",
    "Vertice",
    "Limite",
    "Coordenada",
    # CAR BBox
    "UfSicar",
    "StatusImovelSicar",
    "TipoImovelSicar",
    "UF_BBOXES",
    "detectar_ufs_por_bbox",
    # INCRA WFS (GeoOne)
    "CamadaIncra",
    "StatusCertificacao",
    "CAMADA_LAYER_MAP",
    "CAMADA_DESCRICAO",
    "UF_ID_PARA_SIGLA",
]
