"""
Serviço de consulta de parcelas INCRA por Bounding Box via GeoOne WFS.

Orquestra a chamada ao WFS do GeoOne GeoINCRA
e converte para o modelo de resposta.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from src.core.logging import get_logger
from src.domain.entities.incra_wfs import (
    CAMADA_DESCRICAO,
    UF_ID_PARA_SIGLA,
    CamadaIncra,
)
from src.infrastructure.geoone_wfs.client import (
    GeoOneError,
    GeoOneTimeoutError,
    GeoOneWfsClient,
)

logger = get_logger(__name__)


# ──────────────────────────────────────────────
#  Dataclasses de resultado
# ──────────────────────────────────────────────

@dataclass
class ParcelaIncraResultado:
    """Parcela SIGEF/INCRA resultante da consulta WFS GeoOne."""

    id: str
    parcela_codigo: str
    codigo_imovel: str
    nome_area: str
    status: str
    situacao: str
    rt: str
    art: str
    data_submissao: str | None = None
    data_aprovacao: str | None = None
    registro_matricula: str | None = None
    registro_destaque: str | None = None
    municipio_ibge: int = 0
    uf: str = ""


@dataclass
class FeatureGenericaResultado:
    """Feature genérica para camadas não-SIGEF (quilombolas, assentamentos, etc.)."""

    id: str
    propriedades: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsultaIncraBboxResultado:
    """Resultado completo da consulta INCRA por BBox."""

    total_encontrados: int
    total_retornados: int
    bbox_consultado: dict[str, float]
    camada: str
    camada_descricao: str
    srs: str
    parcelas: list[ParcelaIncraResultado]
    features_genericas: list[FeatureGenericaResultado]


class IncraBboxServiceError(Exception):
    """Erro no serviço de consulta INCRA BBox."""

    def __init__(self, mensagem: str, codigo: str = "INCRA_BBOX_ERROR"):
        self.mensagem = mensagem
        self.codigo = codigo
        super().__init__(mensagem)


# Camadas que retornam schema SIGEF (parcelas)
_CAMADAS_SIGEF = {CamadaIncra.SIGEF_PARTICULAR, CamadaIncra.SIGEF_PUBLICO}


class IncraBboxService:
    """
    Serviço para consulta de parcelas INCRA por Bounding Box.

    Usa o WFS do GeoOne GeoINCRA para buscar parcelas certificadas,
    SNCI, assentamentos, quilombolas e pendentes de titulação
    dentro de uma área geográfica.
    """

    def __init__(self, wfs_client: GeoOneWfsClient) -> None:
        self._wfs_client = wfs_client

    async def consultar(
        self,
        bbox_wfs: str,
        camada: CamadaIncra,
        max_resultados: int = 50,
    ) -> ConsultaIncraBboxResultado:
        """
        Consulta parcelas/territórios INCRA dentro de um Bounding Box.

        Args:
            bbox_wfs: BBox no formato "minLon,minLat,maxLon,maxLat".
            camada: Camada WFS a consultar.
            max_resultados: Máximo de features a retornar (1-5000).

        Returns:
            ConsultaIncraBboxResultado com as features encontradas.

        Raises:
            IncraBboxServiceError: Erro na consulta ou processamento.
        """
        try:
            geojson = await self._chamar_wfs(
                bbox_wfs=bbox_wfs,
                camada=camada.value,
                max_features=max_resultados,
            )
        except GeoOneTimeoutError as e:
            raise IncraBboxServiceError(
                mensagem=str(e),
                codigo="GEOONE_TIMEOUT",
            ) from e
        except GeoOneError as e:
            raise IncraBboxServiceError(
                mensagem=str(e),
                codigo="GEOONE_INDISPONIVEL",
            ) from e

        return self._processar_geojson(
            geojson=geojson,
            bbox_wfs=bbox_wfs,
            camada=camada,
            max_resultados=max_resultados,
        )

    async def _chamar_wfs(
        self,
        bbox_wfs: str,
        camada: str,
        max_features: int,
    ) -> dict[str, Any]:
        """Executa chamada WFS em thread separada (I/O síncrono)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._wfs_client.consultar_bbox,
            bbox_wfs,
            camada,
            max_features,
            False,  # com_geometria sempre False
        )

    def _processar_geojson(
        self,
        geojson: dict[str, Any],
        bbox_wfs: str,
        camada: CamadaIncra,
        max_resultados: int,
    ) -> ConsultaIncraBboxResultado:
        """Processa GeoJSON e converte para resultado tipado."""
        features = geojson.get("features", [])
        total_geoserver = geojson.get("totalFeatures", len(features))
        features = features[:max_resultados]

        coords = bbox_wfs.split(",")
        bbox_dict = {
            "min_lon": float(coords[0]),
            "min_lat": float(coords[1]),
            "max_lon": float(coords[2]),
            "max_lat": float(coords[3]),
        }

        parcelas: list[ParcelaIncraResultado] = []
        features_genericas: list[FeatureGenericaResultado] = []

        if camada in _CAMADAS_SIGEF:
            parcelas = [
                self._feature_para_parcela(f) for f in features
            ]
        else:
            features_genericas = [
                self._feature_para_generica(f) for f in features
            ]

        return ConsultaIncraBboxResultado(
            total_encontrados=total_geoserver if isinstance(total_geoserver, int) else len(features),
            total_retornados=len(parcelas) + len(features_genericas),
            bbox_consultado=bbox_dict,
            camada=camada.value,
            camada_descricao=CAMADA_DESCRICAO.get(camada.value, camada.value),
            srs="EPSG:4674",
            parcelas=parcelas,
            features_genericas=features_genericas,
        )

    @staticmethod
    def _feature_para_parcela(
        feature: dict[str, Any],
    ) -> ParcelaIncraResultado:
        """Converte feature GeoJSON SIGEF em ParcelaIncraResultado."""
        props = feature.get("properties", {})
        uf_id = props.get("uf_id")
        uf_sigla = UF_ID_PARA_SIGLA.get(int(uf_id), "") if uf_id is not None else ""

        # Limpar datas (remover 'Z' se presente)
        data_submi = props.get("data_submi")
        if isinstance(data_submi, str):
            data_submi = data_submi.rstrip("Z")

        data_aprov = props.get("data_aprov")
        if isinstance(data_aprov, str):
            data_aprov = data_aprov.rstrip("Z")

        return ParcelaIncraResultado(
            id=feature.get("id", ""),
            parcela_codigo=props.get("parcela_codigo", ""),
            codigo_imovel=props.get("codigo_imo", ""),
            nome_area=props.get("nome_area", ""),
            status=props.get("status", ""),
            situacao=props.get("situacao_i", ""),
            rt=props.get("rt", ""),
            art=props.get("art", ""),
            data_submissao=data_submi,
            data_aprovacao=data_aprov,
            registro_matricula=props.get("registro_m"),
            registro_destaque=props.get("registro_d"),
            municipio_ibge=props.get("municipio_", 0),
            uf=uf_sigla,
        )

    @staticmethod
    def _feature_para_generica(
        feature: dict[str, Any],
    ) -> FeatureGenericaResultado:
        """Converte feature GeoJSON genérica."""
        return FeatureGenericaResultado(
            id=feature.get("id", ""),
            propriedades=feature.get("properties", {}),
        )
