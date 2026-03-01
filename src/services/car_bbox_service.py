"""
Serviço de consulta de CARs por Bounding Box.

Orquestra a chamada ao WFS do GeoServer do SICAR,
aplica filtros client-side e converte para o modelo de resposta.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.core.logging import get_logger
from src.domain.entities.car_bbox import (
    STATUS_DESCRICAO,
    TIPO_DESCRICAO,
    StatusImovelSicar,
    TipoImovelSicar,
    detectar_ufs_por_bbox,
)
from src.infrastructure.car_wfs.client import (
    CarWfsClient,
    GeoServerError,
    GeoServerTimeoutError,
)

logger = get_logger(__name__)


# ──────────────────────────────────────────────
#  Dataclass de resultado (domínio interno)
# ──────────────────────────────────────────────

@dataclass
class ImovelRuralResultado:
    """Imóvel rural resultante da consulta WFS."""

    id: str
    cod_imovel: str
    status_imovel: str
    status_descricao: str
    tipo_imovel: str
    tipo_descricao: str
    area_hectares: float
    modulos_fiscais: float
    uf: str
    municipio: str
    cod_municipio_ibge: int
    condicao: str | None = None
    data_criacao: datetime | None = None


@dataclass
class ConsultaCarBboxResultado:
    """Resultado completo da consulta de CARs por BBox."""

    total_encontrados: int
    total_retornados: int
    bbox_consultado: dict[str, float]
    ufs_consultadas: list[str]
    srs: str
    filtros_aplicados: dict[str, str]
    imoveis: list[ImovelRuralResultado]


class CarBboxServiceError(Exception):
    """Erro no serviço de consulta CAR BBox."""

    def __init__(self, mensagem: str, codigo: str = "CAR_BBOX_ERROR"):
        self.mensagem = mensagem
        self.codigo = codigo
        super().__init__(mensagem)


class CarBboxService:
    """
    Serviço para consulta de CARs por Bounding Box.

    Usa o WFS do GeoServer do SICAR para buscar imóveis rurais
    dentro de uma área geográfica, aplicando filtros client-side
    (devido a limitações do WAF da Dataprev).
    """

    # Fator de multiplicação para compensar filtros client-side:
    # busca N vezes mais features para garantir resultados após filtragem
    _FATOR_FILTRO = 10

    def __init__(self, wfs_client: CarWfsClient) -> None:
        self._wfs_client = wfs_client

    async def consultar(
        self,
        bbox_wfs: str,
        max_resultados: int = 50,
        status: StatusImovelSicar | None = None,
        tipo_imovel: TipoImovelSicar | None = None,
    ) -> ConsultaCarBboxResultado:
        """
        Consulta CARs dentro de um Bounding Box.

        A UF é detectada automaticamente a partir das coordenadas do BBox.
        Se o BBox intersectar múltiplos estados, todos são consultados.
        Geometria nunca é retornada (payload otimizado).

        Args:
            bbox_wfs: BBox no formato "minLon,minLat,maxLon,maxLat".
            max_resultados: Máximo de imóveis a retornar (1-5000).
            status: Filtro por status do cadastro (aplicado client-side).
            tipo_imovel: Filtro por tipo de imóvel (aplicado client-side).

        Returns:
            ConsultaCarBboxResultado com os imóveis encontrados.

        Raises:
            CarBboxServiceError: Erro na consulta ou processamento.
        """
        # Auto-detectar UFs a partir do BBox
        coords = bbox_wfs.split(",")
        ufs = detectar_ufs_por_bbox(
            min_lon=float(coords[0]),
            min_lat=float(coords[1]),
            max_lon=float(coords[2]),
            max_lat=float(coords[3]),
        )

        if not ufs:
            raise CarBboxServiceError(
                mensagem="O Bounding Box informado não intersecta nenhum estado brasileiro.",
                codigo="BBOX_FORA_DO_BRASIL",
            )

        logger.info(
            "UFs detectadas para consulta",
            ufs=ufs,
            bbox=bbox_wfs,
        )

        tem_filtros = status is not None or tipo_imovel is not None
        max_features_wfs = (
            max_resultados * self._FATOR_FILTRO if tem_filtros else max_resultados
        )

        # Consultar cada UF detectada e agregar resultados
        todas_features: list[dict[str, Any]] = []
        total_encontrados_global = 0

        for uf in ufs:
            try:
                geojson = await self._chamar_wfs(
                    bbox_wfs=bbox_wfs,
                    uf=uf,
                    max_features=max_features_wfs,
                    com_geometria=False,
                )
                features = geojson.get("features", [])
                total_geoserver = geojson.get("totalFeatures", len(features))
                total_encontrados_global += (
                    total_geoserver if isinstance(total_geoserver, int) else len(features)
                )
                todas_features.extend(features)
            except GeoServerTimeoutError as e:
                raise CarBboxServiceError(
                    mensagem=str(e),
                    codigo="GEOSERVER_TIMEOUT",
                ) from e
            except GeoServerError as e:
                # Se uma UF falhar, logar e continuar com as demais
                logger.warning(
                    "Erro ao consultar UF no GeoServer",
                    uf=uf,
                    erro=str(e),
                )
                continue

        return self._processar_features(
            features=todas_features,
            total_encontrados=total_encontrados_global,
            bbox_wfs=bbox_wfs,
            ufs=ufs,
            max_resultados=max_resultados,
            status=status,
            tipo_imovel=tipo_imovel,
        )

    async def _chamar_wfs(
        self,
        bbox_wfs: str,
        uf: str,
        max_features: int,
        com_geometria: bool,
    ) -> dict[str, Any]:
        """Executa chamada WFS em thread separada (I/O síncrono)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._wfs_client.consultar_bbox,
            bbox_wfs,
            uf,
            max_features,
            com_geometria,
        )

    def _processar_features(
        self,
        features: list[dict[str, Any]],
        total_encontrados: int,
        bbox_wfs: str,
        ufs: list[str],
        max_resultados: int,
        status: StatusImovelSicar | None,
        tipo_imovel: TipoImovelSicar | None,
    ) -> ConsultaCarBboxResultado:
        """Aplica filtros client-side e converte para resultado."""
        # Filtros client-side (WAF bloqueia CQL_FILTER no servidor)
        filtros_aplicados: dict[str, str] = {}

        if status is not None:
            filtros_aplicados["status_imovel"] = status.value
            features = [
                f for f in features
                if f.get("properties", {}).get("status_imovel") == status.value
            ]

        if tipo_imovel is not None:
            filtros_aplicados["tipo_imovel"] = tipo_imovel.value
            features = [
                f for f in features
                if f.get("properties", {}).get("tipo_imovel") == tipo_imovel.value
            ]

        # Limitar ao max_resultados após filtragem
        features = features[:max_resultados]

        imoveis = [
            self._feature_para_imovel(f)
            for f in features
        ]

        coords = bbox_wfs.split(",")
        bbox_dict = {
            "min_lon": float(coords[0]),
            "min_lat": float(coords[1]),
            "max_lon": float(coords[2]),
            "max_lat": float(coords[3]),
        }

        return ConsultaCarBboxResultado(
            total_encontrados=total_encontrados,
            total_retornados=len(imoveis),
            bbox_consultado=bbox_dict,
            ufs_consultadas=ufs,
            srs="EPSG:4674",
            filtros_aplicados=filtros_aplicados,
            imoveis=imoveis,
        )

    @staticmethod
    def _feature_para_imovel(
        feature: dict[str, Any],
    ) -> ImovelRuralResultado:
        """Converte uma feature GeoJSON em ImovelRuralResultado."""
        props = feature.get("properties", {})
        status_cod = props.get("status_imovel", "")
        tipo_cod = props.get("tipo_imovel", "")

        data_criacao = None
        dat_criacao_raw = props.get("dat_criacao")
        if dat_criacao_raw:
            try:
                data_criacao = datetime.fromisoformat(
                    str(dat_criacao_raw).replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                data_criacao = None

        return ImovelRuralResultado(
            id=feature.get("id", ""),
            cod_imovel=props.get("cod_imovel", ""),
            status_imovel=status_cod,
            status_descricao=STATUS_DESCRICAO.get(status_cod, status_cod),
            tipo_imovel=tipo_cod,
            tipo_descricao=TIPO_DESCRICAO.get(tipo_cod, tipo_cod),
            area_hectares=props.get("area", 0.0),
            modulos_fiscais=props.get("m_fiscal", 0.0),
            uf=props.get("uf", ""),
            municipio=props.get("municipio", ""),
            cod_municipio_ibge=props.get("cod_municipio_ibge", 0),
            condicao=props.get("condicao"),
            data_criacao=data_criacao,
        )
