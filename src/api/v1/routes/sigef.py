"""
Rotas SIGEF - Versão Mínima para Cliente C#.

Endpoints disponíveis:
- GET /v1/sigef/arquivo/todos/{codigo} - Download ZIP com todos os arquivos
- GET /v1/sigef/arquivo/csv/{codigo}/{tipo} - Download CSV específico
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io
import zipfile

from src.api.v1.dependencies import get_sigef_service, RequireAPIKey
from src.api.v1.schemas import TipoExportacaoEnum
from src.core.exceptions import (
    InvalidParcelaCodeError,
    ParcelaNotFoundError,
    SessionExpiredError,
    SigefError,
)
from src.core.logging import get_logger
from src.domain.entities import TipoExportacao
from src.services.sigef_service import SigefService

logger = get_logger(__name__)

router = APIRouter(prefix="/sigef", tags=["SIGEF"])


@router.get(
    "/arquivo/csv/{codigo}/{tipo}",
    summary="📄 Download direto de CSV",
    description="""
Download de arquivo CSV da parcela SIGEF.

### Tipos disponíveis

| Tipo | Descrição |
|------|-----------|
| `parcela` | Dados gerais da parcela |
| `vertice` | Coordenadas dos vértices |
| `limite` | Polígono de limites |
    """,
    responses={
        200: {
            "description": "Arquivo CSV",
            "content": {"text/csv": {}},
        },
        400: {"description": "Código de parcela inválido"},
        401: {"description": "Sessão expirada"},
        404: {"description": "Parcela não encontrada"},
        502: {"description": "Erro ao comunicar com SIGEF"},
    },
)
async def download_csv_arquivo(
    codigo: str,
    tipo: TipoExportacaoEnum,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """
    Retorna arquivo CSV como stream para download direto.
    """
    try:
        tipo_domain = TipoExportacao(tipo.value)
        
        path = await sigef_service.download_csv(
            codigo=codigo,
            tipo=tipo_domain,
        )
        
        content = path.read_bytes()
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{codigo}_{tipo.value}.csv"',
                "Content-Length": str(len(content)),
                "X-Filename": f"{codigo}_{tipo.value}.csv",
            },
        )
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except ParcelaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get(
    "/arquivo/todos/{codigo}",
    summary="📦 Download completo (ZIP com todos arquivos)",
    description="""
Download de todos os arquivos da parcela em um único ZIP.

### Conteúdo do ZIP

| Arquivo | Descrição |
|---------|-----------|
| `{codigo}_parcela.csv` | Dados gerais |
| `{codigo}_vertice.csv` | Coordenadas |
| `{codigo}_limite.csv` | Limites |
| `{codigo}_memorial.pdf` | Memorial descritivo (se disponível) |
    """,
    responses={
        200: {
            "description": "Arquivo ZIP",
            "content": {"application/zip": {}},
        },
        400: {"description": "Código de parcela inválido"},
        401: {"description": "Sessão expirada"},
        404: {"description": "Parcela não encontrada"},
        502: {"description": "Erro ao comunicar com SIGEF"},
    },
)
async def download_todos_arquivos(
    codigo: str,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """
    Retorna ZIP com todos os arquivos da parcela.
    """
    try:
        # Baixa todos os CSVs
        csv_paths = await sigef_service.download_all_csvs(codigo=codigo)
        
        # Tenta baixar memorial (pode não estar disponível)
        memorial_path = None
        try:
            memorial_path = await sigef_service.download_memorial(codigo=codigo)
        except Exception as e:
            logger.warning(f"Memorial não disponível para {codigo}: {e}")
        
        # Cria ZIP em memória
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Adiciona CSVs
            for tipo, path_str in csv_paths.items():
                from pathlib import Path
                path = Path(path_str)
                if path.exists():
                    zip_file.write(path, f"{codigo}_{tipo}.csv")
            
            # Adiciona memorial se disponível
            if memorial_path and memorial_path.exists():
                zip_file.write(memorial_path, f"{codigo}_memorial.pdf")
        
        zip_buffer.seek(0)
        content = zip_buffer.read()
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{codigo}_completo.zip"',
                "Content-Length": str(len(content)),
                "X-Filename": f"{codigo}_completo.zip",
            },
        )
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except ParcelaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))
