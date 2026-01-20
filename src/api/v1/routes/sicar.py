"""
Rotas SICAR - Download de shapefiles do Sistema de Cadastro Ambiental Rural.

Endpoints para download direto de arquivos do SICAR.
"""

from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api.v1.dependencies import RequireAPIKey
from src.core.logging import get_logger
from src.services.sicar_service import SicarService, AVAILABLE_POLYGONS, AVAILABLE_STATES

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
            }
        },
        "available_polygons": AVAILABLE_POLYGONS,
        "available_states": AVAILABLE_STATES,
    }
