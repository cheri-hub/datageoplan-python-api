"""
Modelos de Request/Response para a API de consulta de CARs por BBOX.

Utiliza Pydantic v2 para validação e serialização.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ──────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────

class UF(str, Enum):
    AC = "AC"
    AL = "AL"
    AM = "AM"
    AP = "AP"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MG = "MG"
    MS = "MS"
    MT = "MT"
    PA = "PA"
    PB = "PB"
    PE = "PE"
    PI = "PI"
    PR = "PR"
    RJ = "RJ"
    RN = "RN"
    RO = "RO"
    RR = "RR"
    RS = "RS"
    SC = "SC"
    SE = "SE"
    SP = "SP"
    TO = "TO"


class StatusImovel(str, Enum):
    ATIVO = "AT"
    PENDENTE = "PE"
    CANCELADO = "CA"
    INSCRITO = "IN"
    RETIFICADO = "RE"
    SUSPENSO = "SU"


class TipoImovel(str, Enum):
    IMOVEL_RURAL = "IRU"
    POVOS_COMUNIDADES_TRADICIONAIS = "PCT"
    ASSENTAMENTO_REFORMA_AGRARIA = "AST"


# ──────────────────────────────────────────────
#  Request Models
# ──────────────────────────────────────────────

class BoundingBox(BaseModel):
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
    def validate_bbox_order(self) -> "BoundingBox":
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
        """Converte para o formato WFS BBOX: 'minLon,minLat,maxLon,maxLat,EPSG:4674'."""
        return f"{self.min_lon},{self.min_lat},{self.max_lon},{self.max_lat}"


class ConsultaCarBboxRequest(BaseModel):
    """Request para consulta de CARs dentro de um Bounding Box."""

    bbox: BoundingBox = Field(
        ...,
        description="Bounding Box geográfico da área de busca",
    )
    uf: UF = Field(
        ...,
        description="Sigla do estado (cada estado é uma camada separada no GeoServer)",
    )
    max_resultados: int = Field(
        default=50,
        ge=1,
        le=5000,
        description="Número máximo de imóveis a retornar",
    )
    incluir_geometria: bool = Field(
        default=False,
        description="Se True, inclui o MultiPolygon de cada imóvel na resposta",
    )
    status: Optional[StatusImovel] = Field(
        default=None,
        description="Filtrar por status do cadastro (filtrado client-side)",
    )
    tipo_imovel: Optional[TipoImovel] = Field(
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
                    "uf": "SP",
                    "max_resultados": 50,
                    "incluir_geometria": False,
                    "status": None,
                    "tipo_imovel": None,
                }
            ]
        }
    }


# ──────────────────────────────────────────────
#  Response Models
# ──────────────────────────────────────────────

class Coordenada(BaseModel):
    """Par de coordenadas [longitude, latitude]."""

    lon: float
    lat: float


class Geometria(BaseModel):
    """Geometria GeoJSON do imóvel."""

    type: str = Field(
        default="MultiPolygon",
        description="Tipo da geometria GeoJSON",
    )
    coordinates: list = Field(
        ...,
        description="Coordenadas no formato GeoJSON MultiPolygon: [[[[lon,lat], ...]]]",
    )


class ImovelRural(BaseModel):
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
    status_imovel: StatusImovel = Field(
        ...,
        description="Status do cadastro",
    )
    status_descricao: str = Field(
        ...,
        description="Descrição legível do status",
        examples=["Ativo"],
    )
    tipo_imovel: TipoImovel = Field(
        ...,
        description="Tipo de imóvel",
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
    condicao: Optional[str] = Field(
        default=None,
        description="Condição de análise do cadastro",
        examples=["Analisado, em conformidade com a Lei nº 12.651/2012"],
    )
    data_criacao: Optional[datetime] = Field(
        default=None,
        description="Data de criação do registro",
        examples=["2015-06-24T12:32:44.749Z"],
    )
    geometria: Optional[Geometria] = Field(
        default=None,
        description="Geometria MultiPolygon do perímetro (presente apenas se incluir_geometria=True)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "sicar_imoveis_sp.1199503",
                    "cod_imovel": "SP-3550605-BA021C304C504869A0BDDA5BA55B40C0",
                    "status_imovel": "AT",
                    "status_descricao": "Ativo",
                    "tipo_imovel": "IRU",
                    "tipo_descricao": "Imóvel Rural",
                    "area_hectares": 0.1025,
                    "modulos_fiscais": 0.0085,
                    "uf": "SP",
                    "municipio": "São Roque",
                    "cod_municipio_ibge": 3550605,
                    "condicao": "Analisado, aguardando atendimento a notificação",
                    "data_criacao": "2015-06-24T12:32:44.749Z",
                    "geometria": None,
                }
            ]
        }
    }


class ConsultaCarBboxResponse(BaseModel):
    """Response da consulta de CARs por Bounding Box."""

    total_encontrados: int = Field(
        ...,
        ge=0,
        description="Total de imóveis que intersectam o BBOX (pode ser maior que os retornados)",
        examples=[424],
    )
    total_retornados: int = Field(
        ...,
        ge=0,
        description="Quantidade de imóveis efetivamente retornados nesta resposta",
        examples=[50],
    )
    bbox_consultado: BoundingBox = Field(
        ...,
        description="O BBOX utilizado na consulta",
    )
    uf: UF = Field(
        ...,
        description="Estado consultado",
    )
    srs: str = Field(
        default="EPSG:4674",
        description="Sistema de referência espacial (SIRGAS 2000)",
    )
    filtros_aplicados: dict = Field(
        default_factory=dict,
        description="Filtros de atributo aplicados (client-side)",
        examples=[{"status_imovel": "AT"}],
    )
    imoveis: list[ImovelRural] = Field(
        default_factory=list,
        description="Lista de imóveis rurais encontrados",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_encontrados": 424,
                    "total_retornados": 2,
                    "bbox_consultado": {
                        "min_lon": -47.1,
                        "min_lat": -23.6,
                        "max_lon": -47.0,
                        "max_lat": -23.5,
                    },
                    "uf": "SP",
                    "srs": "EPSG:4674",
                    "filtros_aplicados": {},
                    "imoveis": [
                        {
                            "id": "sicar_imoveis_sp.1199503",
                            "cod_imovel": "SP-3550605-BA021C304C504869A0BDDA5BA55B40C0",
                            "status_imovel": "AT",
                            "status_descricao": "Ativo",
                            "tipo_imovel": "IRU",
                            "tipo_descricao": "Imóvel Rural",
                            "area_hectares": 0.1025,
                            "modulos_fiscais": 0.0085,
                            "uf": "SP",
                            "municipio": "São Roque",
                            "cod_municipio_ibge": 3550605,
                            "condicao": "Analisado, aguardando atendimento a notificação",
                            "data_criacao": "2015-06-24T12:32:44.749Z",
                            "geometria": None,
                        }
                    ],
                }
            ]
        }
    }


# ──────────────────────────────────────────────
#  Error Response
# ──────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Detalhe de um erro."""

    campo: Optional[str] = Field(
        default=None,
        description="Campo que causou o erro (se aplicável)",
    )
    mensagem: str = Field(
        ...,
        description="Descrição do erro",
    )


class ErrorResponse(BaseModel):
    """Response de erro padronizado."""

    erro: str = Field(
        ...,
        description="Tipo/código do erro",
        examples=["VALIDACAO", "GEOSERVER_INDISPONIVEL", "BBOX_INVALIDO", "UF_INVALIDA"],
    )
    mensagem: str = Field(
        ...,
        description="Mensagem geral do erro",
    )
    detalhes: list[ErrorDetail] = Field(
        default_factory=list,
        description="Detalhes adicionais do erro",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "erro": "BBOX_INVALIDO",
                    "mensagem": "O bounding box informado é inválido",
                    "detalhes": [
                        {
                            "campo": "bbox.min_lon",
                            "mensagem": "min_lon (-47.0) deve ser menor que max_lon (-47.1)",
                        }
                    ],
                }
            ]
        }
    }


# ──────────────────────────────────────────────
#  Helpers de conversão (GeoServer → API)
# ──────────────────────────────────────────────

STATUS_DESCRICAO = {
    "AT": "Ativo",
    "PE": "Pendente",
    "CA": "Cancelado",
    "IN": "Inscrito",
    "RE": "Retificado",
    "SU": "Suspenso",
}

TIPO_DESCRICAO = {
    "IRU": "Imóvel Rural",
    "PCT": "Povos e Comunidades Tradicionais",
    "AST": "Assentamento da Reforma Agrária",
}


def feature_to_imovel(feature: dict, incluir_geometria: bool = False) -> ImovelRural:
    """Converte uma feature GeoJSON do GeoServer para o modelo ImovelRural."""
    props = feature.get("properties", {})
    status = props.get("status_imovel", "")
    tipo = props.get("tipo_imovel", "")

    geometria = None
    if incluir_geometria and feature.get("geometry"):
        geometria = Geometria(**feature["geometry"])

    return ImovelRural(
        id=feature.get("id", ""),
        cod_imovel=props.get("cod_imovel", ""),
        status_imovel=status,
        status_descricao=STATUS_DESCRICAO.get(status, status),
        tipo_imovel=tipo,
        tipo_descricao=TIPO_DESCRICAO.get(tipo, tipo),
        area_hectares=props.get("area", 0),
        modulos_fiscais=props.get("m_fiscal", 0),
        uf=props.get("uf", ""),
        municipio=props.get("municipio", ""),
        cod_municipio_ibge=props.get("cod_municipio_ibge", 0),
        condicao=props.get("condicao"),
        data_criacao=props.get("dat_criacao"),
        geometria=geometria,
    )


def geojson_to_response(
    geojson: dict,
    request: ConsultaCarBboxRequest,
) -> ConsultaCarBboxResponse:
    """Converte o GeoJSON bruto do GeoServer para o response padronizado da API."""
    features = geojson.get("features", [])

    # Filtros client-side
    filtros = {}

    if request.status:
        filtros["status_imovel"] = request.status.value
        features = [
            f for f in features
            if f.get("properties", {}).get("status_imovel") == request.status.value
        ]

    if request.tipo_imovel:
        filtros["tipo_imovel"] = request.tipo_imovel.value
        features = [
            f for f in features
            if f.get("properties", {}).get("tipo_imovel") == request.tipo_imovel.value
        ]

    # Limitar ao max_resultados após filtragem
    features = features[: request.max_resultados]

    imoveis = [
        feature_to_imovel(f, request.incluir_geometria)
        for f in features
    ]

    total_geoserver = geojson.get("totalFeatures", len(features))

    return ConsultaCarBboxResponse(
        total_encontrados=total_geoserver if isinstance(total_geoserver, int) else len(imoveis),
        total_retornados=len(imoveis),
        bbox_consultado=request.bbox,
        uf=request.uf,
        filtros_aplicados=filtros,
        imoveis=imoveis,
    )
