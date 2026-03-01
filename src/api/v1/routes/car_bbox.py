"""
Rota de consulta de CARs por Bounding Box.

Endpoint POST /api/car/bbox que consulta o WFS público do GeoServer do SICAR
e retorna imóveis rurais dentro da área geográfica informada.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import RequireAPIKey, get_car_bbox_service
from src.api.v1.schemas_car_bbox import (
    BoundingBoxSchema,
    CarBboxErrorResponse,
    ConsultaCarBboxRequest,
    ConsultaCarBboxResponse,
    ImovelRuralSchema,
)
from src.core.logging import get_logger
from src.services.car_bbox_service import (
    CarBboxService,
    CarBboxServiceError,
    ConsultaCarBboxResultado,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/car", tags=["SICAR"])


@router.post(
    "/bbox",
    response_model=ConsultaCarBboxResponse,
    summary="Consultar CARs por Bounding Box",
    description=(
        "Consulta imóveis rurais (CARs) dentro de um Bounding Box geográfico "
        "via WFS público do GeoServer do SICAR. "
        "O estado (UF) é detectado automaticamente a partir das coordenadas do BBox. "
        "Se o BBox intersectar múltiplos estados, todos são consultados. "
        "Filtros por status e tipo de imóvel são aplicados client-side "
        "(limitação do WAF da Dataprev)."
    ),
    responses={
        400: {
            "model": CarBboxErrorResponse,
            "description": "BBox fora dos limites do Brasil",
        },
        422: {
            "model": CarBboxErrorResponse,
            "description": "Erro de validação nos dados de entrada",
        },
        502: {
            "model": CarBboxErrorResponse,
            "description": "GeoServer do SICAR indisponível",
        },
        504: {
            "model": CarBboxErrorResponse,
            "description": "Timeout na comunicação com o GeoServer",
        },
    },
)
async def consultar_car_por_bbox(
    request: ConsultaCarBboxRequest,
    _api_key: RequireAPIKey,
    service: CarBboxService = Depends(get_car_bbox_service),
) -> ConsultaCarBboxResponse:
    """
    Consulta CARs dentro de um Bounding Box.

    A UF é detectada automaticamente a partir das coordenadas.
    Retorna lista de imóveis rurais com código CAR, status,
    tipo, área e município.
    """
    try:
        resultado = await service.consultar(
            bbox_wfs=request.bbox.to_wfs_string(),
            max_resultados=request.max_resultados,
            status=request.status,
            tipo_imovel=request.tipo_imovel,
        )
    except CarBboxServiceError as e:
        codigo_http = _mapear_codigo_http(e.codigo)
        logger.error(
            "Erro na consulta CAR BBox",
            erro=e.codigo,
            mensagem=e.mensagem,
        )
        raise HTTPException(
            status_code=codigo_http,
            detail={
                "erro": e.codigo,
                "mensagem": e.mensagem,
                "detalhes": [],
            },
        ) from e

    return _resultado_para_response(resultado, request)


def _mapear_codigo_http(codigo_erro: str) -> int:
    """Mapeia código de erro do serviço para HTTP status code."""
    mapeamento = {
        "GEOSERVER_TIMEOUT": status.HTTP_504_GATEWAY_TIMEOUT,
        "GEOSERVER_INDISPONIVEL": status.HTTP_502_BAD_GATEWAY,
        "BBOX_FORA_DO_BRASIL": status.HTTP_400_BAD_REQUEST,
    }
    return mapeamento.get(codigo_erro, status.HTTP_502_BAD_GATEWAY)


def _resultado_para_response(
    resultado: "ConsultaCarBboxResultado",
    request: ConsultaCarBboxRequest,
) -> ConsultaCarBboxResponse:
    """Converte resultado do serviço para schema de response."""
    imoveis_schema = [
        ImovelRuralSchema(
            id=im.id,
            cod_imovel=im.cod_imovel,
            status_imovel=im.status_imovel,
            status_descricao=im.status_descricao,
            tipo_imovel=im.tipo_imovel,
            tipo_descricao=im.tipo_descricao,
            area_hectares=im.area_hectares,
            modulos_fiscais=im.modulos_fiscais,
            uf=im.uf,
            municipio=im.municipio,
            cod_municipio_ibge=im.cod_municipio_ibge,
            condicao=im.condicao,
            data_criacao=im.data_criacao,
        )
        for im in resultado.imoveis
    ]

    return ConsultaCarBboxResponse(
        total_encontrados=resultado.total_encontrados,
        total_retornados=resultado.total_retornados,
        bbox_consultado=BoundingBoxSchema(**resultado.bbox_consultado),
        ufs_consultadas=resultado.ufs_consultadas,
        srs=resultado.srs,
        filtros_aplicados=resultado.filtros_aplicados,
        imoveis=imoveis_schema,
    )
