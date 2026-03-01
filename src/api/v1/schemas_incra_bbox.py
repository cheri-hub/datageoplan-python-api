"""
Schemas Pydantic para o endpoint de consulta INCRA por Bounding Box (GeoOne WFS).

Separado do schemas.py principal para seguir o princípio de impacto mínimo.
"""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.domain.entities.incra_wfs import CamadaIncra


# ──────────────────────────────────────────────
#  Request Models
# ──────────────────────────────────────────────

class BoundingBoxIncraSchema(BaseModel):
    """Bounding Box geográfico em EPSG:4674 (SIRGAS 2000)."""

    min_lon: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude mínima (oeste)",
        examples=[-47.1],
    )
    min_lat: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude mínima (sul)",
        examples=[-23.6],
    )
    max_lon: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude máxima (leste)",
        examples=[-47.0],
    )
    max_lat: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude máxima (norte)",
        examples=[-23.5],
    )

    @model_validator(mode="after")
    def validar_ordem_bbox(self) -> "BoundingBoxIncraSchema":
        """Valida que min < max para lon e lat."""
        if self.min_lon >= self.max_lon:
            raise ValueError(
                f"min_lon ({self.min_lon}) deve ser menor que max_lon ({self.max_lon})"
            )
        if self.min_lat >= self.max_lat:
            raise ValueError(
                f"min_lat ({self.min_lat}) deve ser menor que max_lat ({self.max_lat})"
            )
        return self

    def to_wfs_string(self) -> str:
        """Converte para o formato WFS BBOX: 'minLon,minLat,maxLon,maxLat'."""
        return f"{self.min_lon},{self.min_lat},{self.max_lon},{self.max_lat}"


class ConsultaIncraBboxRequest(BaseModel):
    """Request para consulta de parcelas INCRA dentro de um Bounding Box."""

    bbox: BoundingBoxIncraSchema = Field(
        ...,
        description="Bounding Box geográfico da área de busca",
    )
    camada: CamadaIncra = Field(
        default=CamadaIncra.SIGEF_PARTICULAR,
        description=(
            "Camada WFS a consultar. "
            "sigef_particular e sigef_publico retornam dados tipados de parcelas SIGEF. "
            "Demais camadas retornam propriedades genéricas."
        ),
    )
    max_resultados: int = Field(
        default=50,
        ge=1,
        le=5000,
        description="Número máximo de features a retornar",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bbox": {
                        "min_lon": -47.1,
                        "min_lat": -23.6,
                        "max_lon": -47.0,
                        "max_lat": -23.5,
                    },
                    "camada": "sigef_particular",
                    "max_resultados": 50,
                }
            ]
        }
    }


# ──────────────────────────────────────────────
#  Response Models
# ──────────────────────────────────────────────

class ParcelaIncraSchema(BaseModel):
    """Dados de uma parcela SIGEF certificada retornada pela consulta."""

    id: str = Field(
        ...,
        description="ID interno do GeoServer (ex: certificado_sigef_privado.682540)",
        examples=["certificado_sigef_privado.682540"],
    )
    parcela_codigo: str = Field(
        ...,
        description="Código UUID da parcela SIGEF",
        examples=["19333463-2591-45b7-926d-6f9e55fd777a"],
    )
    codigo_imovel: str = Field(
        ...,
        description="Código do imóvel no cadastro",
        examples=["6321040151560"],
    )
    nome_area: str = Field(
        ...,
        description="Nome/denominação da área",
        examples=["SÍTIO PEREIRA"],
    )
    status: str = Field(
        ...,
        description="Status de certificação",
        examples=["CERTIFICADA"],
    )
    situacao: str = Field(
        ...,
        description="Situação do imóvel no cadastro",
        examples=["REGISTRADA"],
    )
    rt: str = Field(
        ...,
        description="Código do Responsável Técnico",
        examples=["LBMX"],
    )
    art: str = Field(
        ...,
        description="Número da ART/TRT",
        examples=["CFT2302865046-SP"],
    )
    data_submissao: str | None = Field(
        default=None,
        description="Data de submissão ao SIGEF",
        examples=["2023-09-18"],
    )
    data_aprovacao: str | None = Field(
        default=None,
        description="Data de aprovação/certificação",
        examples=["2023-09-18"],
    )
    registro_matricula: str | None = Field(
        default=None,
        description="Número(s) de registro de matrícula",
        examples=["18727, 18728, 18729"],
    )
    registro_destaque: str | None = Field(
        default=None,
        description="Número de registro de destaque",
    )
    municipio_ibge: int = Field(
        ...,
        description="Código IBGE do município",
        examples=[3550605],
    )
    uf: str = Field(
        ...,
        max_length=2,
        description="Sigla do estado (derivada do código IBGE)",
        examples=["SP"],
    )


class FeatureGenericaSchema(BaseModel):
    """Feature genérica para camadas não-SIGEF."""

    id: str = Field(
        ...,
        description="ID interno do GeoServer",
    )
    propriedades: dict[str, Any] = Field(
        default_factory=dict,
        description="Propriedades da feature (schema varia por camada)",
    )


class ConsultaIncraBboxResponse(BaseModel):
    """Response da consulta INCRA por Bounding Box."""

    total_encontrados: int = Field(
        ...,
        ge=0,
        description="Total de features que intersectam o BBox no GeoServer",
        examples=[105],
    )
    total_retornados: int = Field(
        ...,
        ge=0,
        description="Quantidade efetivamente retornada nesta resposta",
        examples=[50],
    )
    bbox_consultado: BoundingBoxIncraSchema = Field(
        ...,
        description="O BBox utilizado na consulta",
    )
    camada: str = Field(
        ...,
        description="Camada consultada",
        examples=["sigef_particular"],
    )
    camada_descricao: str = Field(
        ...,
        description="Descrição legível da camada",
        examples=["Imóveis Certificados SIGEF - Particular"],
    )
    srs: str = Field(
        default="EPSG:4674",
        description="Sistema de referência espacial (SIRGAS 2000)",
    )
    parcelas: list[ParcelaIncraSchema] = Field(
        default_factory=list,
        description="Parcelas SIGEF (preenchido para camadas sigef_particular/sigef_publico)",
    )
    features_genericas: list[FeatureGenericaSchema] = Field(
        default_factory=list,
        description="Features genéricas (preenchido para demais camadas)",
    )


# ──────────────────────────────────────────────
#  Error Response
# ──────────────────────────────────────────────

class IncraBboxErrorResponse(BaseModel):
    """Response de erro padronizado para consulta INCRA BBox."""

    erro: str = Field(
        ...,
        description="Tipo/código do erro",
        examples=["GEOONE_INDISPONIVEL"],
    )
    mensagem: str = Field(
        ...,
        description="Mensagem geral do erro",
    )
    detalhes: list[dict[str, str]] = Field(
        default_factory=list,
        description="Detalhes adicionais do erro",
    )
