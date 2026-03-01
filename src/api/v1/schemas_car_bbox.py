"""
Schemas Pydantic para o endpoint de consulta de CARs por Bounding Box.

Separado do schemas.py principal para seguir o princípio de impacto mínimo.
"""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from src.domain.entities.car_bbox import (
    StatusImovelSicar,
    TipoImovelSicar,
)


# ──────────────────────────────────────────────
#  Request Models
# ──────────────────────────────────────────────

class BoundingBoxSchema(BaseModel):
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
    def validar_ordem_bbox(self) -> "BoundingBoxSchema":
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


class ConsultaCarBboxRequest(BaseModel):
    """Request para consulta de CARs dentro de um Bounding Box."""

    bbox: BoundingBoxSchema = Field(
        ...,
        description="Bounding Box geográfico da área de busca",
    )
    max_resultados: int = Field(
        default=50,
        ge=1,
        le=5000,
        description="Número máximo de imóveis a retornar",
    )
    status: StatusImovelSicar | None = Field(
        default=None,
        description="Filtrar por status do cadastro (filtrado client-side)",
    )
    tipo_imovel: TipoImovelSicar | None = Field(
        default=None,
        description="Filtrar por tipo de imóvel (filtrado client-side)",
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
                    "max_resultados": 50,
                    "status": None,
                    "tipo_imovel": None,
                }
            ]
        }
    }


# ──────────────────────────────────────────────
#  Response Models
# ──────────────────────────────────────────────


class ImovelRuralSchema(BaseModel):
    """Dados de um imóvel rural (CAR) retornado pela consulta."""

    id: str = Field(
        ...,
        description="ID interno do GeoServer (ex: sicar_imoveis_sp.1199503)",
        examples=["sicar_imoveis_sp.1199503"],
    )
    cod_imovel: str = Field(
        ...,
        description="Código CAR completo: UF-CodMunIBGE-Hash",
        examples=["SP-3550605-BA021C304C504869A0BDDA5BA55B40C0"],
    )
    status_imovel: str = Field(
        ...,
        description="Código do status",
        examples=["AT"],
    )
    status_descricao: str = Field(
        ...,
        description="Descrição legível do status",
        examples=["Ativo"],
    )
    tipo_imovel: str = Field(
        ...,
        description="Código do tipo de imóvel",
        examples=["IRU"],
    )
    tipo_descricao: str = Field(
        ...,
        description="Descrição legível do tipo",
        examples=["Imóvel Rural"],
    )
    area_hectares: float = Field(
        ...,
        ge=0,
        description="Área do imóvel em hectares",
        examples=[21.7038],
    )
    modulos_fiscais: float = Field(
        ...,
        ge=0,
        description="Área em módulos fiscais",
        examples=[1.8092],
    )
    uf: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Sigla do estado",
        examples=["SP"],
    )
    municipio: str = Field(
        ...,
        description="Nome do município",
        examples=["São Roque"],
    )
    cod_municipio_ibge: int = Field(
        ...,
        description="Código IBGE do município",
        examples=[3550605],
    )
    condicao: str | None = Field(
        default=None,
        description="Condição de análise do cadastro",
    )
    data_criacao: datetime | None = Field(
        default=None,
        description="Data de criação do registro",
    )


class ConsultaCarBboxResponse(BaseModel):
    """Response da consulta de CARs por Bounding Box."""

    total_encontrados: int = Field(
        ...,
        ge=0,
        description="Total de imóveis que intersectam o BBox no GeoServer",
        examples=[424],
    )
    total_retornados: int = Field(
        ...,
        ge=0,
        description="Quantidade efetivamente retornada nesta resposta",
        examples=[50],
    )
    bbox_consultado: BoundingBoxSchema = Field(
        ...,
        description="O BBox utilizado na consulta",
    )
    ufs_consultadas: list[str] = Field(
        ...,
        description="Estados detectados automaticamente a partir do BBox",
        examples=[["SP"]],
    )
    srs: str = Field(
        default="EPSG:4674",
        description="Sistema de referência espacial (SIRGAS 2000)",
    )
    filtros_aplicados: dict[str, str] = Field(
        default_factory=dict,
        description="Filtros de atributo aplicados client-side",
        examples=[{"status_imovel": "AT"}],
    )
    imoveis: list[ImovelRuralSchema] = Field(
        default_factory=list,
        description="Lista de imóveis rurais encontrados",
    )


# ──────────────────────────────────────────────
#  Error Response
# ──────────────────────────────────────────────

class CarBboxErrorDetail(BaseModel):
    """Detalhe de um erro na consulta CAR BBox."""

    campo: str | None = Field(
        default=None,
        description="Campo que causou o erro (se aplicável)",
    )
    mensagem: str = Field(
        ...,
        description="Descrição do erro",
    )


class CarBboxErrorResponse(BaseModel):
    """Response de erro padronizado para consulta CAR BBox."""

    erro: str = Field(
        ...,
        description="Tipo/código do erro",
        examples=["GEOSERVER_INDISPONIVEL"],
    )
    mensagem: str = Field(
        ...,
        description="Mensagem geral do erro",
    )
    detalhes: list[CarBboxErrorDetail] = Field(
        default_factory=list,
        description="Detalhes adicionais do erro",
    )
