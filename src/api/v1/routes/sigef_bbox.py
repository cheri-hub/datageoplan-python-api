"""
Rota de consulta de parcelas INCRA por Bounding Box via GeoOne WFS.

Endpoint POST /api/sigef/bbox que consulta o WFS do GeoOne GeoINCRA
e retorna parcelas certificadas / territórios dentro da área geográfica.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import RequireAPIKey, get_incra_bbox_service
from src.api.v1.schemas_incra_bbox import (
    BoundingBoxIncraSchema,
    ConsultaIncraBboxRequest,
    ConsultaIncraBboxResponse,
    FeatureGenericaSchema,
    IncraBboxErrorResponse,
    ParcelaIncraSchema,
)
from src.core.logging import get_logger
from src.services.incra_bbox_service import (
    ConsultaIncraBboxResultado,
    IncraBboxService,
    IncraBboxServiceError,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/sigef", tags=["SIGEF"])


@router.post(
    "/bbox",
    response_model=ConsultaIncraBboxResponse,
    summary="Consultar parcelas INCRA por Bounding Box",
    description=(
        "Consulta parcelas certificadas SIGEF, SNCI, assentamentos, quilombolas "
        "e pendentes de titulação dentro de um Bounding Box geográfico "
        "via WFS do GeoOne GeoINCRA. "
        "Camadas SIGEF (particular/público) retornam dados tipados de parcelas. "
        "Demais camadas retornam propriedades genéricas."
    ),
    responses={
        422: {
            "model": IncraBboxErrorResponse,
            "description": "Erro de validação nos dados de entrada",
        },
        502: {
            "model": IncraBboxErrorResponse,
            "description": "GeoOne indisponível ou camada não acessível",
        },
        504: {
            "model": IncraBboxErrorResponse,
            "description": "Timeout na comunicação com o GeoOne",
        },
    },
)
async def consultar_incra_por_bbox(
    request: ConsultaIncraBboxRequest,
    _api_key: RequireAPIKey,
    service: IncraBboxService = Depends(get_incra_bbox_service),
) -> ConsultaIncraBboxResponse:
    """
    Consulta parcelas INCRA dentro de um Bounding Box.

    Utiliza o WFS público do GeoOne GeoINCRA para buscar
    parcelas certificadas e outros territórios fundiários.
    As camadas são nacionais (sem separação por UF).
    """
    try:
        resultado = await service.consultar(
            bbox_wfs=request.bbox.to_wfs_string(),
            camada=request.camada,
            max_resultados=request.max_resultados,
        )
    except IncraBboxServiceError as e:
        codigo_http = _mapear_codigo_http(e.codigo)
        logger.error(
            "Erro na consulta INCRA BBox",
            erro=e.codigo,
            mensagem=e.mensagem,
            camada=request.camada.value,
        )
        raise HTTPException(
            status_code=codigo_http,
            detail={
                "erro": e.codigo,
                "mensagem": e.mensagem,
                "detalhes": [],
            },
        ) from e

    return _resultado_para_response(resultado)


def _mapear_codigo_http(codigo_erro: str) -> int:
    """Mapeia código de erro do serviço para HTTP status code."""
    mapeamento = {
        "GEOONE_TIMEOUT": status.HTTP_504_GATEWAY_TIMEOUT,
        "GEOONE_INDISPONIVEL": status.HTTP_502_BAD_GATEWAY,
    }
    return mapeamento.get(codigo_erro, status.HTTP_502_BAD_GATEWAY)


def _resultado_para_response(
    resultado: ConsultaIncraBboxResultado,
) -> ConsultaIncraBboxResponse:
    """Converte resultado do serviço para schema de response."""
    parcelas_schema = [
        ParcelaIncraSchema(
            id=p.id,
            parcela_codigo=p.parcela_codigo,
            codigo_imovel=p.codigo_imovel,
            nome_area=p.nome_area,
            status=p.status,
            situacao=p.situacao,
            rt=p.rt,
            art=p.art,
            data_submissao=p.data_submissao,
            data_aprovacao=p.data_aprovacao,
            registro_matricula=p.registro_matricula,
            registro_destaque=p.registro_destaque,
            municipio_ibge=p.municipio_ibge,
            uf=p.uf,
        )
        for p in resultado.parcelas
    ]

    features_schema = [
        FeatureGenericaSchema(
            id=f.id,
            propriedades=f.propriedades,
        )
        for f in resultado.features_genericas
    ]

    return ConsultaIncraBboxResponse(
        total_encontrados=resultado.total_encontrados,
        total_retornados=resultado.total_retornados,
        bbox_consultado=BoundingBoxIncraSchema(**resultado.bbox_consultado),
        camada=resultado.camada,
        camada_descricao=resultado.camada_descricao,
        srs=resultado.srs,
        parcelas=parcelas_schema,
        features_genericas=features_schema,
    )
