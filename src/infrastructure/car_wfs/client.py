"""
Cliente WFS para consulta de CARs por Bounding Box no GeoServer do SICAR.

Consome o serviço WFS público:
  https://geoserver.car.gov.br/geoserver/sicar/wfs

Limitações conhecidas:
  - BBOX e CQL_FILTER são mutuamente exclusivos no WFS
  - WAF (Dataprev) bloqueia CQL_FILTER isolado
  - SSL requer SECLEVEL=1 para handshake
"""

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.core.logging import get_logger

logger = get_logger(__name__)

# Constantes do GeoServer SICAR
GEOSERVER_WFS_URL = "https://geoserver.car.gov.br/geoserver/sicar/wfs"
WFS_VERSION = "1.1.0"
WFS_SRS = "EPSG:4674"
WFS_OUTPUT_FORMAT = "application/json"
WFS_TIMEOUT_SECONDS = 60
WFS_USER_AGENT = "datageoplan-api/1.0"

# Campos retornados quando geometria não é solicitada
PROPERTY_NAMES_SEM_GEOMETRIA = (
    "cod_imovel,status_imovel,dat_criacao,area,"
    "condicao,uf,municipio,cod_municipio_ibge,m_fiscal,tipo_imovel"
)


class GeoServerError(Exception):
    """Erro na comunicação com o GeoServer do SICAR."""

    def __init__(self, mensagem: str, codigo_http: int | None = None):
        self.mensagem = mensagem
        self.codigo_http = codigo_http
        super().__init__(mensagem)


class GeoServerTimeoutError(GeoServerError):
    """Timeout na comunicação com o GeoServer."""

    def __init__(self, mensagem: str = "GeoServer não respondeu dentro do tempo limite"):
        super().__init__(mensagem)


class CarWfsClient:
    """
    Cliente para o WFS do GeoServer do SICAR.

    Realiza consultas GetFeature por Bounding Box, retornando
    GeoJSON com os imóveis rurais da região.
    """

    def __init__(
        self,
        url_base: str = GEOSERVER_WFS_URL,
        timeout: int = WFS_TIMEOUT_SECONDS,
    ) -> None:
        self._url_base = url_base
        self._timeout = timeout
        self._ssl_context = self._criar_ssl_context()

    @staticmethod
    def _criar_ssl_context() -> ssl.SSLContext:
        """Cria contexto SSL com SECLEVEL=1 para compatibilidade com o GeoServer."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        return ctx

    def consultar_bbox(
        self,
        bbox_wfs: str,
        uf: str,
        max_features: int = 50,
        com_geometria: bool = False,
    ) -> dict[str, Any]:
        """
        Consulta imóveis rurais dentro de um Bounding Box via WFS GetFeature.

        Args:
            bbox_wfs: BBox no formato "minLon,minLat,maxLon,maxLat" (EPSG:4674).
            uf: Sigla do estado em minúsculo (ex: "sp").
            max_features: Número máximo de features a solicitar ao GeoServer.
            com_geometria: Se False, exclui geometria via PROPERTYNAME (payload ~80% menor).

        Returns:
            GeoJSON FeatureCollection como dict.

        Raises:
            GeoServerError: Erro HTTP ou de conexão com o GeoServer.
            GeoServerTimeoutError: Timeout na requisição.
        """
        uf_lower = uf.lower()
        layer = f"sicar_imoveis_{uf_lower}"

        params: dict[str, str] = {
            "SERVICE": "WFS",
            "VERSION": WFS_VERSION,
            "REQUEST": "GetFeature",
            "TYPENAMES": layer,
            "BBOX": f"{bbox_wfs},{WFS_SRS}",
            "OUTPUTFORMAT": WFS_OUTPUT_FORMAT,
            "MAXFEATURES": str(max_features),
        }

        if not com_geometria:
            params["PROPERTYNAME"] = PROPERTY_NAMES_SEM_GEOMETRIA

        url = f"{self._url_base}?{urllib.parse.urlencode(params)}"

        logger.info(
            "Consultando WFS GeoServer SICAR",
            layer=layer,
            bbox=bbox_wfs,
            max_features=max_features,
            com_geometria=com_geometria,
        )

        return self._executar_requisicao(url)

    def _executar_requisicao(self, url: str) -> dict[str, Any]:
        """Executa requisição HTTP ao GeoServer e retorna JSON."""
        req = urllib.request.Request(url)
        req.add_header("User-Agent", WFS_USER_AGENT)

        try:
            with urllib.request.urlopen(
                req, timeout=self._timeout, context=self._ssl_context
            ) as resp:
                dados = json.loads(resp.read().decode("utf-8"))

            total = dados.get("totalFeatures", 0)
            retornados = dados.get("numberReturned", len(dados.get("features", [])))
            logger.info(
                "Resposta WFS recebida",
                total_features=total,
                retornados=retornados,
            )
            return dados

        except urllib.error.HTTPError as e:
            logger.error(
                "Erro HTTP do GeoServer",
                status_code=e.code,
                reason=e.reason,
            )
            raise GeoServerError(
                f"GeoServer retornou HTTP {e.code}: {e.reason}",
                codigo_http=e.code,
            ) from e

        except urllib.error.URLError as e:
            if "timed out" in str(e.reason).lower():
                logger.error("Timeout na conexão com GeoServer")
                raise GeoServerTimeoutError(
                    f"GeoServer não respondeu em {self._timeout}s. Tente com um BBox menor."
                ) from e

            logger.error("Erro de conexão com GeoServer", reason=str(e.reason))
            raise GeoServerError(
                f"Não foi possível conectar ao GeoServer: {e.reason}"
            ) from e

        except TimeoutError as e:
            logger.error("Timeout na requisição ao GeoServer")
            raise GeoServerTimeoutError(
                f"GeoServer não respondeu em {self._timeout}s. Tente com um BBox menor."
            ) from e
