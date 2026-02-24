"""
Rotas SICAR - Download de shapefiles do Sistema de Cadastro Ambiental Rural.

Endpoints para download direto de arquivos do SICAR.
"""

from enum import Enum
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api.v1.dependencies import RequireAPIKey
from src.api.v1.schemas import (
    TemaCAR,
    GrupoCAR,
    GrupoTemasCAR,
    ResultadoProcessamentoCAR,
    ProcessedStateRequest,
    ProcessedCARRequest,
    PaletaCoresResponse,
    DemonstrativoCAR,
)
from src.core.logging import get_logger
from src.services.sicar_service import SicarService, AVAILABLE_POLYGONS, AVAILABLE_STATES
from src.infrastructure.sicar_package.car_reference import (
    MODELO_CAR,
    buscar_tema,
    listar_grupos,
    listar_temas_por_grupo,
    obter_paleta_cores,
)
from src.infrastructure.sicar_package.sld_generator import gerar_sld_por_nome
from src.services.car_consulta_service import CarConsultaService, CarConsultaError

logger = get_logger(__name__)

router = APIRouter(prefix="/sicar", tags=["SICAR"])


# ===== Enums =====

class PolygonType(str, Enum):
    """Tipos de polígono disponíveis no SICAR."""
    AREA_PROPERTY = "AREA_PROPERTY"
    APPS = "APPS"
    NATIVE_VEGETATION = "NATIVE_VEGETATION"
    HYDROGRAPHY = "HYDROGRAPHY"
    LEGAL_RESERVE = "LEGAL_RESERVE"
    RESTRICTED_USE = "RESTRICTED_USE"
    CONSOLIDATED_AREA = "CONSOLIDATED_AREA"
    ADMINISTRATIVE_SERVICE = "ADMINISTRATIVE_SERVICE"
    AREA_FALL = "AREA_FALL"


class StateCode(str, Enum):
    """Estados brasileiros."""
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"


# ===== Request Schemas =====

class StateDownloadRequest(BaseModel):
    """Schema para download de polígono de um estado."""
    state: StateCode = Field(..., description="Sigla do estado (ex: SP)")
    polygon: PolygonType = Field(..., description="Tipo de polígono")

    model_config = {
        "json_schema_extra": {
            "example": {
                "state": "SP",
                "polygon": "AREA_PROPERTY"
            }
        }
    }


class CarDownloadRequest(BaseModel):
    """Schema para download por número CAR."""
    car_number: str = Field(
        ..., 
        description="Número do CAR (ex: SP-3538709-4861E981046E49BC81720C879459E554)",
        min_length=10
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "car_number": "SP-3538709-4861E981046E49BC81720C879459E554"
            }
        }
    }


# ===== Endpoints =====

@router.post(
    "/stream/state",
    summary="Download shapefile por estado",
    response_description="Arquivo ZIP contendo o shapefile",
)
async def stream_download_state(
    body: StateDownloadRequest,
    _api_key: RequireAPIKey,
):
    """
    Baixa um shapefile de polígono de um estado e retorna o arquivo diretamente.
    
    ## ⚠️ Tempo de Resposta
    Este endpoint pode demorar **10-60 segundos** devido à resolução de captcha do SICAR.
    Configure timeout adequado no cliente (recomendado: 2 minutos).
    
    ## Polígonos Disponíveis
    - `AREA_PROPERTY` - Área do Imóvel
    - `APPS` - Áreas de Preservação Permanente
    - `NATIVE_VEGETATION` - Vegetação Nativa
    - `HYDROGRAPHY` - Hidrografia
    - `LEGAL_RESERVE` - Reserva Legal
    - `RESTRICTED_USE` - Uso Restrito
    - `CONSOLIDATED_AREA` - Área Consolidada
    - `ADMINISTRATIVE_SERVICE` - Servidão Administrativa
    - `AREA_FALL` - Área de Pousio
    
    ## Exemplo cURL
    ```bash
    curl -X POST "http://localhost:8000/api/v1/sicar/stream/state" \\
      -H "Authorization: Bearer sua-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{"state": "SP", "polygon": "AREA_PROPERTY"}' \\
      --output SP_AREA_PROPERTY.zip
    ```
    """
    try:
        service = SicarService()
        
        file_bytes, filename = service.download_polygon_as_bytes(
            state=body.state.value,
            polygon=body.polygon.value
        )
        
        return StreamingResponse(
            iter([file_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no download SICAR por estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao baixar arquivo: {str(e)}"
        )


@router.post(
    "/stream/car",
    summary="Download shapefile por CAR",
    response_description="Arquivo ZIP contendo o shapefile da propriedade",
)
async def stream_download_car(
    body: CarDownloadRequest,
    _api_key: RequireAPIKey,
):
    """
    Baixa shapefile de uma propriedade específica pelo número CAR.
    
    ## ⚠️ Tempo de Resposta
    Este endpoint pode demorar **10-60 segundos** devido à busca da propriedade
    e resolução de captcha. Configure timeout adequado.
    
    ## Formato do CAR
    O número do CAR segue o padrão: `UF-CODIGO_MUNICIPIO-HASH`
    - Exemplo: `SP-3538709-4861E981046E49BC81720C879459E554`
    
    ## Exemplo cURL
    ```bash
    curl -X POST "http://localhost:8000/api/v1/sicar/stream/car" \\
      -H "Authorization: Bearer sua-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{"car_number": "SP-3538709-4861E981046E49BC81720C879459E554"}' \\
      --output propriedade.zip
    ```
    """
    try:
        service = SicarService()
        
        file_bytes, filename = service.download_car_as_bytes(
            car_number=body.car_number
        )
        
        return StreamingResponse(
            iter([file_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no download SICAR por CAR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao baixar arquivo: {str(e)}"
        )


@router.get(
    "/info",
    summary="Informações sobre endpoints SICAR",
)
async def sicar_info(_api_key: RequireAPIKey):
    """Retorna informações sobre os endpoints SICAR disponíveis."""
    return {
        "service": "SICAR - Sistema de Cadastro Ambiental Rural",
        "endpoints": {
            "stream/state": {
                "method": "POST",
                "description": "Download de shapefile por estado",
                "timeout_recommended": "2 minutos"
            },
            "stream/car": {
                "method": "POST",
                "description": "Download de shapefile por número CAR",
                "timeout_recommended": "2 minutos"
            },
            "stream/state/processed": {
                "method": "POST",
                "description": "Download de shapefile processado por estado com SLD",
                "timeout_recommended": "5 minutos"
            },
            "stream/car/processed": {
                "method": "POST",
                "description": "Download de shapefile de CAR processado com SLD",
                "timeout_recommended": "5 minutos"
            },
            "temas": {
                "method": "GET",
                "description": "Lista todos os grupos de temas CAR"
            },
            "sld/{tema}": {
                "method": "GET",
                "description": "Gera arquivo SLD para um tema específico"
            },
            "cores": {
                "method": "GET",
                "description": "Retorna paleta de cores de todos os temas"
            }
        },
        "available_polygons": AVAILABLE_POLYGONS,
        "available_states": AVAILABLE_STATES,
    }


# ===== Endpoints de Download Processado =====

@router.post(
    "/stream/state/processed",
    summary="Download shapefile processado por estado",
    response_description="Arquivo ZIP contendo shapefiles organizados com SLD",
)
async def stream_download_state_processed(
    body: ProcessedStateRequest,
    _api_key: RequireAPIKey,
):
    """
    Baixa um shapefile de polígono de um estado, processa e retorna organizado.
    
    ## ⚠️ Tempo de Resposta
    Este endpoint pode demorar **2-5 minutos** devido ao download + processamento.
    Configure timeout adequado no cliente (recomendado: 10 minutos).
    
    ## Processamento Inclui:
    - Download do SICAR
    - Organização por grupos temáticos
    - Geração de arquivos SLD (estilos)
    - Padronização de nomes e estrutura
    
    ## Exemplo cURL
    ```bash
    curl -X POST "http://localhost:8000/api/v1/sicar/stream/state/processed" \\
      -H "Authorization: Bearer sua-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{"state": "SP", "polygon": "AREA_PROPERTY", "include_sld": true}' \\
      --output SP_processado.zip
    ```
    """
    try:
        service = SicarService()
        
        file_bytes, filename, resultado = service.download_and_process_state(
            state=body.state,
            polygon=body.polygon,
            include_sld=body.include_sld
        )
        
        return StreamingResponse(
            iter([file_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes)),
                "X-CAR-Temas-Processados": str(resultado.get("temas_processados", 0)),
                "X-CAR-Feicoes-Total": str(resultado.get("feicoes_total", 0)),
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no download processado SICAR por estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


@router.post(
    "/stream/car/processed",
    summary="Download shapefile de CAR processado",
    response_description="Arquivo ZIP contendo shapefiles organizados com SLD",
)
async def stream_download_car_processed(
    body: ProcessedCARRequest,
    _api_key: RequireAPIKey,
):
    """
    Baixa shapefile de uma propriedade específica, processa e retorna organizado.
    
    ## ⚠️ Tempo de Resposta
    Este endpoint pode demorar **2-5 minutos** devido ao download + processamento.
    Configure timeout adequado no cliente (recomendado: 10 minutos).
    
    ## Processamento Inclui:
    - Busca e download da propriedade no SICAR
    - Organização por grupos temáticos
    - Geração de arquivos SLD (estilos)
    - Padronização de nomes e estrutura
    
    ## Exemplo cURL
    ```bash
    curl -X POST "http://localhost:8000/api/v1/sicar/stream/car/processed" \\
      -H "Authorization: Bearer sua-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{"car_number": "SP-3538709-XXX", "include_sld": true}' \\
      --output car_processado.zip
    ```
    """
    try:
        service = SicarService()
        
        file_bytes, filename, resultado = service.download_and_process_car(
            car_number=body.car_number,
            include_sld=body.include_sld
        )
        
        return StreamingResponse(
            iter([file_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes)),
                "X-CAR-Recibo": resultado.get("recibo", ""),
                "X-CAR-Temas-Processados": str(resultado.get("temas_processados", 0)),
                "X-CAR-Feicoes-Total": str(resultado.get("feicoes_total", 0)),
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no download processado SICAR por CAR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


# ===== Endpoints de Temas CAR =====

@router.get(
    "/temas",
    summary="Lista grupos de temas CAR",
    response_model=list[GrupoCAR],
)
async def listar_grupos_temas(_api_key: RequireAPIKey):
    """
    Lista todos os grupos de temas CAR disponíveis.
    
    Os grupos organizam os temas por categoria:
    - Área do Imóvel
    - Servidão Administrativa
    - Cobertura do Solo
    - Área de Preservação Permanente
    - Reserva Legal
    - Área de Uso Restrito
    - Resumo
    """
    grupos = listar_grupos()
    return [GrupoCAR(**grupo) for grupo in grupos]


@router.get(
    "/temas/{grupo}",
    summary="Lista temas de um grupo específico",
    response_model=GrupoTemasCAR,
)
async def listar_temas_grupo(
    grupo: str,
    _api_key: RequireAPIKey,
):
    """
    Lista todos os temas de um grupo CAR específico.
    
    ## Grupos disponíveis:
    - `_Totalizadores`
    - `Area_do_Imovel`
    - `Area_de_Uso_Restrito`
    - `Servidao_Administrativa`
    - `Cobertura_do_Solo`
    - `Area_de_Preservacao_Permanente`
    - `Reserva_Legal`
    """
    if grupo not in MODELO_CAR:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grupo '{grupo}' não encontrado. Grupos disponíveis: {list(MODELO_CAR.keys())}"
        )
    
    classe_dados = MODELO_CAR[grupo]
    temas = [TemaCAR(**tema) for tema in classe_dados["temas_possiveis"]]
    
    return GrupoTemasCAR(
        classe=grupo,
        nome_grupo=classe_dados["nome_grupo"],
        ordem=classe_dados["ordem"],
        temas=temas
    )


@router.get(
    "/sld/{tema}",
    summary="Gera SLD para um tema",
    response_class=Response,
)
async def gerar_sld_tema(
    tema: str,
    _api_key: RequireAPIKey,
):
    """
    Gera arquivo SLD (Styled Layer Descriptor) para um tema CAR.
    
    Use o nome do `arquivo_modelo` retornado pelos endpoints de temas.
    
    ## Exemplo
    - `/sld/Area_do_Imovel`
    - `/sld/Reserva_Legal_Proposta`
    - `/sld/APP_Rios_ate_10_metros`
    """
    sld_content = gerar_sld_por_nome(tema)
    
    if sld_content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tema '{tema}' não encontrado"
        )
    
    return Response(
        content=sld_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename={tema}.sld"
        }
    )


@router.get(
    "/cores",
    summary="Paleta de cores dos temas CAR",
    response_model=dict[str, PaletaCoresResponse],
)
async def obter_paleta(_api_key: RequireAPIKey):
    """
    Retorna a paleta de cores de todos os temas CAR.
    
    Útil para criar visualizações customizadas ou integrar
    com outros sistemas GIS.
    """
    paleta = obter_paleta_cores()
    return {
        nome: PaletaCoresResponse(**dados)
        for nome, dados in paleta.items()
    }


# ===== Endpoints de Consulta CAR (Demonstrativo) =====

@router.get(
    "/consulta/{car_code}",
    summary="Consulta dados do registro CAR",
    response_model=DemonstrativoCAR,
    responses={
        200: {"description": "Dados do demonstrativo CAR"},
        400: {"description": "Código CAR inválido"},
        404: {"description": "Registro CAR não encontrado"},
        502: {"description": "Erro ao comunicar com car.gov.br"},
    },
)
async def consultar_car(
    car_code: str,
    _api_key: RequireAPIKey,
):
    """
    Retorna JSON com todas as informações do registro CAR informado.
    
    Os dados são obtidos diretamente do sistema oficial car.gov.br e incluem:
    
    - **Situação do Cadastro** — status, condição de análise
    - **Dados do Imóvel** — área, módulos fiscais, município, coordenadas, datas
    - **Cobertura do Solo** — vegetação nativa, área consolidada, servidão
    - **Reserva Legal** — situação, áreas propostas/averbadas
    - **APP** — áreas de preservação permanente
    - **Uso Restrito** — áreas de uso restrito
    - **Regularidade Ambiental** — passivo/excedente, áreas a recompor
    
    ## Formato do Código CAR
    `UF-CODIGO_MUNICIPIO-HASH`  
    Exemplo: `SP-3522307-B4A8A1B13D664F0981FB59901F2871CD`
    
    ## Exemplo cURL
    ```bash
    curl -X GET "http://localhost:8000/api/v1/sicar/consulta/SP-3522307-B4A8A1B13D664F0981FB59901F2871CD" \\
      -H "X-API-Key: sua-api-key"
    ```
    """
    car_code = car_code.strip()
    if len(car_code) < 10 or car_code.count("-") < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código CAR inválido. Formato esperado: UF-CODIGOMUNICIPIO-HASH",
        )

    try:
        service = CarConsultaService()
        dados = service.consultar_demonstrativo(car_code)
        
        # Remover dados brutos da resposta tipada
        dados_sem_brutos = {k: v for k, v in dados.items() if k != "_dados_brutos"}
        return DemonstrativoCAR(**dados_sem_brutos)
        
    except CarConsultaError as e:
        logger.error(f"Erro ao consultar CAR {car_code}: {e}")
        
        msg = str(e)
        if "404" in msg or "não encontrado" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro CAR não encontrado: {car_code}",
            )
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao consultar car.gov.br: {msg}",
        )
    except Exception as e:
        logger.error(f"Erro inesperado ao consultar CAR {car_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.get(
    "/consulta/{car_code}/pdf",
    summary="PDF do demonstrativo CAR",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "PDF do demonstrativo",
            "content": {"application/pdf": {}},
        },
        400: {"description": "Código CAR inválido"},
        404: {"description": "Registro CAR não encontrado"},
        502: {"description": "Erro ao comunicar com car.gov.br"},
    },
)
async def consultar_car_pdf(
    car_code: str,
    _api_key: RequireAPIKey,
):
    """
    Retorna PDF do demonstrativo do registro CAR, no formato similar ao oficial.
    
    O PDF contém todas as seções do demonstrativo:
    - Situação do Cadastro
    - Dados do Imóvel Rural
    - Cobertura do Solo
    - Reserva Legal
    - Áreas de Preservação Permanente (APP)
    - Uso Restrito
    - Regularidade Ambiental
    - Informações Gerais
    
    ## Formato do Código CAR
    `UF-CODIGO_MUNICIPIO-HASH`
    
    ## Exemplo cURL
    ```bash
    curl -X GET "http://localhost:8000/api/v1/sicar/consulta/SP-3522307-B4A8A1B13D664F0981FB59901F2871CD/pdf" \\
      -H "X-API-Key: sua-api-key" \\
      --output demonstrativo.pdf
    ```
    """
    car_code = car_code.strip()
    if len(car_code) < 10 or car_code.count("-") < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código CAR inválido. Formato esperado: UF-CODIGOMUNICIPIO-HASH",
        )

    try:
        service = CarConsultaService()
        pdf_bytes = service.gerar_pdf_demonstrativo(car_code)
        
        safe_name = car_code.replace("/", "_")
        filename = f"Demonstrativo_{safe_name}.pdf"
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
        
    except CarConsultaError as e:
        logger.error(f"Erro ao gerar PDF CAR {car_code}: {e}")
        
        msg = str(e)
        if "404" in msg or "não encontrado" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro CAR não encontrado: {car_code}",
            )
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao consultar car.gov.br: {msg}",
        )
    except Exception as e:
        logger.error(f"Erro inesperado ao gerar PDF CAR {car_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )
