"""
Cliente WFS para consulta de parcelas INCRA no GeoOne.

Consome o serviço WFS:
  https://geoonecloud.com/geoserver/GeoINCRA/wfs

Características:
  - Camadas nacionais (sem split por UF)
  - SSL requer SECLEVEL=1 para handshake
  - Suporta PROPERTYNAME para excluir geometria
"""

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.core.logging import get_logger
from src.domain.entities.incra_wfs import (
    CAMADA_LAYER_MAP,
    PROPERTY_NAMES_SIGEF,
)

logger = get_logger(__name__)

# Constantes do GeoOne
GEOONE_WFS_URL = "https://geoonecloud.com/geoserver/GeoINCRA/wfs"
WFS_VERSION = "1.1.0"
WFS_SRS = "EPSG:4674"
WFS_OUTPUT_FORMAT = "application/json"
WFS_TIMEOUT_SECONDS = 60
WFS_USER_AGENT = "datageoplan-api/1.0"

# Camadas SIGEF que suportam PROPERTYNAME otimizado
_CAMADAS_SIGEF = {"sigef_particular", "sigef_publico"}


class GeoOneError(Exception):
    """Erro na comunicação com o GeoOne."""

    def __init__(self, mensagem: str, codigo_http: int | None = None):
        self.mensagem = mensagem
        self.codigo_http = codigo_http
        super().__init__(mensagem)


class GeoOneTimeoutError(GeoOneError):
    """Timeout na comunicação com o GeoOne."""

    def __init__(self, mensagem: str = "GeoOne não respondeu dentro do tempo limite"):
        super().__init__(mensagem)


class GeoOneWfsClient:
    """
    Cliente para o WFS do GeoOne GeoINCRA.

    Realiza consultas GetFeature por Bounding Box, retornando
    GeoJSON com as parcelas/territórios da região.
    """

    def __init__(
        self,
        url_base: str = GEOONE_WFS_URL,
        timeout: int = WFS_TIMEOUT_SECONDS,
    ) -> None:
        self._url_base = url_base
        self._timeout = timeout
        self._ssl_context = self._criar_ssl_context()

    @staticmethod
    def _criar_ssl_context() -> ssl.SSLContext:
        """Cria contexto SSL com SECLEVEL=1 para compatibilidade."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        return ctx

    def consultar_bbox(
        self,
        bbox_wfs: str,
        camada: str,
        max_features: int = 50,
        com_geometria: bool = False,
    ) -> dict[str, Any]:
        """
        Consulta features dentro de um Bounding Box via WFS GetFeature.

        Args:
            bbox_wfs: BBox no formato "minLon,minLat,maxLon,maxLat" (EPSG:4674).
            camada: Chave da camada (ex: "sigef_particular").
            max_features: Número máximo de features a solicitar.
            com_geometria: Se False, exclui geometria via PROPERTYNAME
                           (apenas para camadas SIGEF).

        Returns:
            GeoJSON FeatureCollection como dict.

        Raises:
            GeoOneError: Erro HTTP ou de conexão.
            GeoOneTimeoutError: Timeout na requisição.
        """
        layer = CAMADA_LAYER_MAP.get(camada)
        if not layer:
            raise GeoOneError(f"Camada desconhecida: {camada}")

        params: dict[str, str] = {
            "SERVICE": "WFS",
            "VERSION": WFS_VERSION,
            "REQUEST": "GetFeature",
            "TYPENAMES": layer,
            "BBOX": f"{bbox_wfs},{WFS_SRS}",
            "OUTPUTFORMAT": WFS_OUTPUT_FORMAT,
            "MAXFEATURES": str(max_features),
        }

        # Excluir geometria apenas para camadas SIGEF (schema conhecido)
        if not com_geometria and camada in _CAMADAS_SIGEF:
            params["PROPERTYNAME"] = PROPERTY_NAMES_SIGEF

        url = f"{self._url_base}?{urllib.parse.urlencode(params)}"

        logger.info(
            "Consultando WFS GeoOne",
            layer=layer,
            bbox=bbox_wfs,
            max_features=max_features,
            com_geometria=com_geometria,
        )

        return self._executar_requisicao(url)

    def _executar_requisicao(self, url: str) -> dict[str, Any]:
        """Executa requisição HTTP ao GeoOne e retorna JSON."""
        req = urllib.request.Request(url)
        req.add_header("User-Agent", WFS_USER_AGENT)

        try:
            with urllib.request.urlopen(
                req, timeout=self._timeout, context=self._ssl_context
            ) as resp:
                content = resp.read()
                if not content:
                    raise GeoOneError(
                        "GeoOne retornou resposta vazia. "
                        "A camada pode não estar disponível."
                    )
                dados = json.loads(content.decode("utf-8"))

            total = dados.get("totalFeatures", 0)
            retornados = dados.get("numberReturned", len(dados.get("features", [])))
            logger.info(
                "Resposta WFS GeoOne recebida",
                total_features=total,
                retornados=retornados,
            )
            return dados

        except json.JSONDecodeError as e:
            logger.error("GeoOne retornou resposta não-JSON (possível XML de erro)")
            raise GeoOneError(
                "GeoOne retornou resposta inválida. "
                "A camada pode não suportar o formato solicitado."
            ) from e

        except urllib.error.HTTPError as e:
            logger.error(
                "Erro HTTP do GeoOne",
                status_code=e.code,
                reason=e.reason,
            )
            raise GeoOneError(
                f"GeoOne retornou HTTP {e.code}: {e.reason}",
                codigo_http=e.code,
            ) from e

        except urllib.error.URLError as e:
            if "timed out" in str(e.reason).lower():
                logger.error("Timeout na conexão com GeoOne")
                raise GeoOneTimeoutError(
                    f"GeoOne não respondeu em {self._timeout}s. "
                    "Tente com um BBox menor."
                ) from e

            logger.error("Erro de conexão com GeoOne", reason=str(e.reason))
            raise GeoOneError(
                f"Não foi possível conectar ao GeoOne: {e.reason}"
            ) from e

        except TimeoutError as e:
            logger.error("Timeout na requisição ao GeoOne")
            raise GeoOneTimeoutError(
                f"GeoOne não respondeu em {self._timeout}s. "
                "Tente com um BBox menor."
            ) from e
