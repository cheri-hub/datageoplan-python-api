"""
Rotas SIGEF.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import io
import zipfile

from src.api.v1.dependencies import get_sigef_service, RequireAPIKey
from src.api.v1.schemas import (
    BatchDownloadRequest,
    BatchDownloadResponse,
    DownloadAllRequest,
    DownloadAllResponse,
    DownloadRequest,
    DownloadResponse,
    ParcelaDetalhesResponse,
    ParcelaInfoResponse,
    TipoExportacaoEnum,
)
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
    "/parcela/{codigo}",
    response_model=ParcelaInfoResponse,
    summary="Obtém informações de uma parcela",
    description="Retorna dados básicos de uma parcela do SIGEF.",
)
async def get_parcela(
    codigo: str,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
) -> ParcelaInfoResponse:
    """Obtém informações de uma parcela."""
    try:
        parcela = await sigef_service.get_parcela_info(codigo)
        
        return ParcelaInfoResponse(
            codigo=parcela.codigo,
            denominacao=parcela.denominacao,
            area_ha=parcela.area_ha,
            perimetro_m=parcela.perimetro_m,
            municipio=parcela.municipio,
            uf=parcela.uf,
            situacao=parcela.situacao.value if parcela.situacao else None,
            url=parcela.get_url_sigef(),
        )
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except ParcelaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/download",
    response_model=DownloadResponse,
    summary="Baixa CSV de uma parcela",
    description="Faz download de um arquivo CSV (parcela, vértice ou limite).",
)
async def download_csv(
    request: DownloadRequest,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
) -> DownloadResponse:
    """Baixa CSV de uma parcela."""
    try:
        # Converte enum da API para enum do domínio
        tipo = TipoExportacao(request.tipo.value)
        
        path = await sigef_service.download_csv(
            codigo=request.codigo,
            tipo=tipo,
        )
        
        return DownloadResponse(
            success=True,
            message=f"CSV de {request.tipo.value} baixado com sucesso",
            arquivo=str(path),
            tamanho_bytes=path.stat().st_size,
        )
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except ParcelaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/download/all",
    response_model=DownloadAllResponse,
    summary="Baixa todos os CSVs de uma parcela",
    description="Faz download dos três arquivos: parcela, vértice e limite.",
)
async def download_all_csvs(
    request: DownloadAllRequest,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
) -> DownloadAllResponse:
    """Baixa todos os CSVs de uma parcela."""
    try:
        results = await sigef_service.download_all_csvs(codigo=request.codigo)
        
        return DownloadAllResponse(
            success=True,
            message="Todos os CSVs baixados com sucesso",
            arquivos={k: str(v) for k, v in results.items()},
        )
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except ParcelaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/download/batch",
    response_model=BatchDownloadResponse,
    summary="Baixa CSVs de múltiplas parcelas",
    description="Faz download em lote para várias parcelas.",
)
async def download_batch(
    request: BatchDownloadRequest,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
) -> BatchDownloadResponse:
    """Baixa CSVs de múltiplas parcelas."""
    try:
        # Converte enums
        tipos = None
        if request.tipos:
            tipos = [TipoExportacao(t.value) for t in request.tipos]
        
        results = await sigef_service.download_batch(
            codigos=request.codigos,
            tipos=tipos,
        )
        
        # Conta sucessos e falhas
        sucesso = sum(1 for r in results.values() if "error" not in r)
        falhas = sum(1 for r in results.values() if "error" in r)
        
        return BatchDownloadResponse(
            success=falhas == 0,
            message=f"Download concluído: {sucesso} sucesso, {falhas} falhas",
            total=len(request.codigos),
            sucesso=sucesso,
            falhas=falhas,
            resultados={k: {kk: str(vv) for kk, vv in v.items()} for k, v in results.items()},
        )
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except Exception as e:
        logger.exception("Erro no download batch")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/download/{codigo}/{tipo}",
    summary="Download direto do arquivo CSV",
    description="Retorna o arquivo CSV diretamente para download.",
    response_class=FileResponse,
)
async def download_file(
    codigo: str,
    tipo: TipoExportacaoEnum,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """Retorna arquivo CSV para download direto."""
    try:
        tipo_domain = TipoExportacao(tipo.value)
        
        path = await sigef_service.download_csv(
            codigo=codigo,
            tipo=tipo_domain,
        )
        
        return FileResponse(
            path=path,
            filename=path.name,
            media_type="text/csv",
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
    "/memorial/{codigo}",
    summary="Download do memorial descritivo (PDF)",
    description="Retorna o memorial descritivo da parcela em formato PDF.",
    response_class=FileResponse,
)
async def download_memorial(
    codigo: str,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """Retorna memorial descritivo (PDF) para download direto."""
    try:
        path = await sigef_service.download_memorial(codigo=codigo)
        
        return FileResponse(
            path=path,
            filename=path.name,
            media_type="application/pdf",
        )
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except ParcelaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/open-browser/{codigo}",
    summary="Abre página da parcela no navegador autenticado",
    description="Abre a página de detalhes da parcela usando o navegador Playwright já autenticado.",
)
async def open_browser(
    codigo: str,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
) -> dict:
    """Abre página da parcela no navegador autenticado."""
    try:
        await sigef_service.open_parcela_browser(codigo)
        
        return {
            "success": True,
            "message": f"Página da parcela {codigo} aberta no navegador autenticado",
        }
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get(
    "/detalhes/{codigo}",
    response_model=ParcelaDetalhesResponse,
    summary="Obtém detalhes completos de uma parcela",
    description="Extrai todas as informações da página HTML da parcela.",
)
async def get_detalhes(
    codigo: str,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
) -> ParcelaDetalhesResponse:
    """Obtém detalhes completos da parcela."""
    try:
        detalhes = await sigef_service.get_parcela_detalhes(codigo)
        return ParcelaDetalhesResponse(**detalhes)
        
    except InvalidParcelaCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except SigefError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ============== ENDPOINTS PARA DOWNLOAD DIRETO (C# / Aplicações Externas) ==============

@router.get(
    "/arquivo/csv/{codigo}/{tipo}",
    tags=["Download Direto"],
    summary="📄 Download direto de CSV",
    description="""
## Download de arquivo CSV

Retorna o arquivo CSV diretamente como stream de bytes, ideal para integração com aplicações externas.

### Tipos disponíveis

| Tipo | Descrição | Conteúdo |
|------|-----------|----------|
| `parcela` | Dados gerais | Código, denominação, área, situação |
| `vertice` | Coordenadas | Latitude, longitude de cada vértice |
| `limite` | Limites | Polígono de limites da parcela |

### Exemplo cURL

```bash
curl -o parcela.csv \\
  -H "Authorization: Bearer sua-api-key" \\
  "http://localhost:8000/api/v1/sigef/arquivo/csv/a1b2c3d4-e5f6-7890-abcd-ef1234567890/parcela"
```

### Exemplo C# (.NET)

```csharp
using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", "sua-api-key");

// Download do CSV
var response = await client.GetAsync(
    $"http://localhost:8000/api/v1/sigef/arquivo/csv/{codigo}/parcela"
);
response.EnsureSuccessStatusCode();

// Salvar em arquivo
var bytes = await response.Content.ReadAsByteArrayAsync();
await File.WriteAllBytesAsync("parcela.csv", bytes);

// OU ler diretamente como string
var csvContent = await response.Content.ReadAsStringAsync();
```

### Exemplo Python

```python
import httpx

response = httpx.get(
    f"http://localhost:8000/api/v1/sigef/arquivo/csv/{codigo}/parcela",
    headers={"Authorization": "Bearer sua-api-key"}
)
response.raise_for_status()

with open("parcela.csv", "wb") as f:
    f.write(response.content)
```

### Headers de Resposta

| Header | Descrição |
|--------|-----------|
| `Content-Disposition` | Nome sugerido para o arquivo |
| `Content-Length` | Tamanho em bytes |
| `X-Filename` | Nome do arquivo |
    """,
    responses={
        200: {
            "description": "Arquivo CSV baixado com sucesso",
            "content": {
                "text/csv": {
                    "example": "codigo;denominacao;area_ha;municipio;uf\\na1b2c3d4...;Fazenda Exemplo;150.5;São Paulo;SP"
                }
            },
            "headers": {
                "Content-Disposition": {
                    "description": "Nome do arquivo para download",
                    "schema": {"type": "string", "example": 'attachment; filename="codigo_parcela.csv"'}
                },
                "X-Filename": {
                    "description": "Nome do arquivo",
                    "schema": {"type": "string", "example": "codigo_parcela.csv"}
                }
            }
        },
        400: {"description": "Código de parcela inválido (não é UUID)"},
        401: {"description": "Sessão expirada - faça login novamente"},
        404: {"description": "Parcela não encontrada no SIGEF"},
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
    
    Ideal para consumo por aplicações C#, Java, etc.
    """
    try:
        tipo_domain = TipoExportacao(tipo.value)
        
        path = await sigef_service.download_csv(
            codigo=codigo,
            tipo=tipo_domain,
        )
        
        # Lê o conteúdo do arquivo
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
    "/arquivo/memorial/{codigo}",
    tags=["Download Direto"],
    summary="📄 Download do memorial descritivo (PDF)",
    description="""
## Download do Memorial Descritivo

Retorna o memorial descritivo da parcela em formato PDF.

O memorial descritivo contém informações legais e técnicas da parcela,
incluindo descrição dos limites, confrontantes e coordenadas.

### Exemplo cURL

```bash
curl -o memorial.pdf \\
  -H "Authorization: Bearer sua-api-key" \\
  "http://localhost:8000/api/v1/sigef/arquivo/memorial/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Exemplo C# (.NET)

```csharp
using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", "sua-api-key");

var response = await client.GetAsync(
    $"http://localhost:8000/api/v1/sigef/arquivo/memorial/{codigo}"
);
response.EnsureSuccessStatusCode();

var pdfBytes = await response.Content.ReadAsByteArrayAsync();
await File.WriteAllBytesAsync("memorial.pdf", pdfBytes);

// Abrir PDF no viewer padrão
System.Diagnostics.Process.Start(new ProcessStartInfo
{
    FileName = "memorial.pdf",
    UseShellExecute = true
});
```

### Exemplo Python

```python
import httpx

response = httpx.get(
    f"http://localhost:8000/api/v1/sigef/arquivo/memorial/{codigo}",
    headers={"Authorization": "Bearer sua-api-key"}
)
response.raise_for_status()

with open("memorial.pdf", "wb") as f:
    f.write(response.content)
```
    """,
    responses={
        200: {
            "description": "Arquivo PDF do memorial descritivo",
            "content": {"application/pdf": {}},
            "headers": {
                "Content-Disposition": {
                    "description": "Nome do arquivo para download",
                    "schema": {"type": "string", "example": 'attachment; filename="codigo_memorial.pdf"'}
                }
            }
        },
        400: {"description": "Código de parcela inválido"},
        401: {"description": "Sessão expirada"},
        404: {"description": "Memorial não encontrado"},
        502: {"description": "Erro ao comunicar com SIGEF"},
    },
)
async def download_memorial_arquivo(
    codigo: str,
    _api_key: RequireAPIKey,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """
    Retorna memorial descritivo (PDF) como stream para download direto.
    """
    try:
        path = await sigef_service.download_memorial(codigo=codigo)
        
        content = path.read_bytes()
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{codigo}_memorial.pdf"',
                "Content-Length": str(len(content)),
                "X-Filename": f"{codigo}_memorial.pdf",
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
    tags=["Download Direto"],
    summary="📦 Download completo (ZIP com todos arquivos)",
    description="""
## Download de Todos os Arquivos

Retorna um arquivo ZIP contendo todos os arquivos disponíveis da parcela.

### Conteúdo do ZIP

| Arquivo | Descrição |
|---------|-----------|
| `{codigo}_parcela.csv` | Dados gerais da parcela |
| `{codigo}_vertice.csv` | Coordenadas dos vértices |
| `{codigo}_limite.csv` | Polígono de limites |
| `{codigo}_memorial.pdf` | Memorial descritivo (se disponível) |

### Exemplo cURL

```bash
curl -o parcela_completa.zip \\
  -H "Authorization: Bearer sua-api-key" \\
  "http://localhost:8000/api/v1/sigef/arquivo/todos/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Exemplo C# (.NET)

```csharp
using System.IO.Compression;

using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", "sua-api-key");

// Download do ZIP
var response = await client.GetAsync(
    $"http://localhost:8000/api/v1/sigef/arquivo/todos/{codigo}"
);
response.EnsureSuccessStatusCode();

var zipBytes = await response.Content.ReadAsByteArrayAsync();

// Salvar ZIP
await File.WriteAllBytesAsync("parcela_completa.zip", zipBytes);

// OU extrair diretamente
using var zipStream = new MemoryStream(zipBytes);
using var archive = new ZipArchive(zipStream, ZipArchiveMode.Read);
archive.ExtractToDirectory("./parcela_extraida", overwriteFiles: true);

// Listar arquivos extraídos
foreach (var entry in archive.Entries)
{
    Console.WriteLine($"Arquivo: {entry.FullName}, Tamanho: {entry.Length} bytes");
}
```

### Exemplo Python

```python
import httpx
import zipfile
import io

response = httpx.get(
    f"http://localhost:8000/api/v1/sigef/arquivo/todos/{codigo}",
    headers={"Authorization": "Bearer sua-api-key"}
)
response.raise_for_status()

# Extrair ZIP
with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
    zf.extractall("./parcela_extraida")
    
    # Listar arquivos
    for name in zf.namelist():
        print(f"Extraído: {name}")
```
    """,
    responses={
        200: {
            "description": "Arquivo ZIP com todos os arquivos",
            "content": {"application/zip": {}},
            "headers": {
                "Content-Disposition": {
                    "description": "Nome do arquivo",
                    "schema": {"type": "string", "example": 'attachment; filename="codigo_completo.zip"'}
                },
                "Content-Length": {
                    "description": "Tamanho em bytes",
                    "schema": {"type": "integer"}
                }
            }
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


@router.get(
    "/arquivo/lote",
    tags=["Download Direto"],
    summary="📦 Download em lote (múltiplas parcelas)",
    description="""
## Download em Lote

Retorna um arquivo ZIP contendo os arquivos de **múltiplas parcelas** organizados em pastas.

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `codigos` | string | ✅ Sim | Códigos SIGEF separados por vírgula (máx 50) |
| `tipos` | string | ❌ Não | Tipos de arquivo: parcela,vertice,limite (default: todos) |

### Estrutura do ZIP

```
lote_3_parcelas.zip
├── uuid-parcela-1/
│   ├── uuid-parcela-1_parcela.csv
│   ├── uuid-parcela-1_vertice.csv
│   └── uuid-parcela-1_limite.csv
├── uuid-parcela-2/
│   ├── uuid-parcela-2_parcela.csv
│   ├── uuid-parcela-2_vertice.csv
│   └── uuid-parcela-2_limite.csv
└── uuid-parcela-3/
    └── ERRO.txt  (se houver falha)
```

### Headers de Resposta

| Header | Descrição |
|--------|-----------|
| `X-Total-Parcelas` | Quantidade total de parcelas solicitadas |
| `X-Sucesso` | Quantidade de parcelas baixadas com sucesso |
| `X-Falhas` | Quantidade de parcelas com falha |

### Exemplo cURL

```bash
# Múltiplas parcelas
curl -o lote.zip \\
  -H "Authorization: Bearer sua-api-key" \\
  "http://localhost:8000/api/v1/sigef/arquivo/lote?codigos=uuid1,uuid2,uuid3"

# Com tipos específicos
curl -o lote.zip \\
  -H "Authorization: Bearer sua-api-key" \\
  "http://localhost:8000/api/v1/sigef/arquivo/lote?codigos=uuid1,uuid2&tipos=parcela,vertice"
```

### Exemplo C# (.NET)

```csharp
using System.IO.Compression;

public class GovAuthDownloader
{
    private readonly HttpClient _client;
    
    public async Task<BatchDownloadResult> DownloadLoteAsync(
        IEnumerable<string> codigosParcela,
        IEnumerable<string>? tipos = null)
    {
        // Construir URL
        var codigos = string.Join(",", codigosParcela);
        var url = $"http://localhost:8000/api/v1/sigef/arquivo/lote?codigos={codigos}";
        
        if (tipos?.Any() == true)
        {
            url += $"&tipos={string.Join(",", tipos)}";
        }
        
        // Fazer requisição
        var response = await _client.GetAsync(url);
        response.EnsureSuccessStatusCode();
        
        // Extrair estatísticas dos headers
        var result = new BatchDownloadResult
        {
            TotalParcelas = int.Parse(
                response.Headers.GetValues("X-Total-Parcelas").First()),
            Sucesso = int.Parse(
                response.Headers.GetValues("X-Sucesso").First()),
            Falhas = int.Parse(
                response.Headers.GetValues("X-Falhas").First())
        };
        
        // Salvar ZIP
        var zipBytes = await response.Content.ReadAsByteArrayAsync();
        var outputPath = $"lote_{result.TotalParcelas}_parcelas.zip";
        await File.WriteAllBytesAsync(outputPath, zipBytes);
        result.ArquivoZip = outputPath;
        
        // Ou extrair diretamente
        using var zipStream = new MemoryStream(zipBytes);
        using var archive = new ZipArchive(zipStream, ZipArchiveMode.Read);
        
        var extractPath = "./parcelas_extraidas";
        archive.ExtractToDirectory(extractPath, overwriteFiles: true);
        
        // Processar cada pasta de parcela
        foreach (var dir in Directory.GetDirectories(extractPath))
        {
            var parcelaId = Path.GetFileName(dir);
            
            // Verificar se teve erro
            var erroFile = Path.Combine(dir, "ERRO.txt");
            if (File.Exists(erroFile))
            {
                var erro = await File.ReadAllTextAsync(erroFile);
                result.Erros[parcelaId] = erro;
            }
            else
            {
                result.ArquivosPorParcela[parcelaId] = 
                    Directory.GetFiles(dir).ToList();
            }
        }
        
        return result;
    }
}

public class BatchDownloadResult
{
    public int TotalParcelas { get; set; }
    public int Sucesso { get; set; }
    public int Falhas { get; set; }
    public string ArquivoZip { get; set; } = "";
    public Dictionary<string, List<string>> ArquivosPorParcela { get; } = new();
    public Dictionary<string, string> Erros { get; } = new();
}

// Uso
var downloader = new GovAuthDownloader();
var result = await downloader.DownloadLoteAsync(
    new[] { "uuid1", "uuid2", "uuid3" },
    new[] { "parcela", "vertice" }
);

Console.WriteLine($"Baixadas: {result.Sucesso}/{result.TotalParcelas}");
if (result.Falhas > 0)
{
    foreach (var (parcela, erro) in result.Erros)
    {
        Console.WriteLine($"Erro em {parcela}: {erro}");
    }
}
```

### Exemplo Python

```python
import httpx
import zipfile
import io
from pathlib import Path

def download_lote(codigos: list[str], tipos: list[str] | None = None):
    params = {"codigos": ",".join(codigos)}
    if tipos:
        params["tipos"] = ",".join(tipos)
    
    response = httpx.get(
        "http://localhost:8000/api/v1/sigef/arquivo/lote",
        params=params,
        headers={"Authorization": "Bearer sua-api-key"}
    )
    response.raise_for_status()
    
    # Estatísticas
    total = int(response.headers["X-Total-Parcelas"])
    sucesso = int(response.headers["X-Sucesso"])
    falhas = int(response.headers["X-Falhas"])
    print(f"Baixadas: {sucesso}/{total} (falhas: {falhas})")
    
    # Extrair ZIP
    output_dir = Path("./parcelas_extraidas")
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(output_dir)
        
        # Verificar erros
        for parcela_dir in output_dir.iterdir():
            erro_file = parcela_dir / "ERRO.txt"
            if erro_file.exists():
                print(f"Erro em {parcela_dir.name}: {erro_file.read_text()}")
            else:
                arquivos = list(parcela_dir.glob("*.csv"))
                print(f"{parcela_dir.name}: {len(arquivos)} arquivos")

# Uso
download_lote(
    codigos=["uuid1", "uuid2", "uuid3"],
    tipos=["parcela", "vertice"]
)
```
    """,
    responses={
        200: {
            "description": "Arquivo ZIP com pastas por parcela",
            "content": {"application/zip": {}},
            "headers": {
                "Content-Disposition": {
                    "description": "Nome do arquivo",
                    "schema": {"type": "string", "example": 'attachment; filename="lote_3_parcelas.zip"'}
                },
                "Content-Length": {
                    "description": "Tamanho em bytes",
                    "schema": {"type": "integer"}
                },
                "X-Total-Parcelas": {
                    "description": "Quantidade total de parcelas solicitadas",
                    "schema": {"type": "integer", "example": 3}
                },
                "X-Sucesso": {
                    "description": "Quantidade de parcelas baixadas com sucesso",
                    "schema": {"type": "integer", "example": 2}
                },
                "X-Falhas": {
                    "description": "Quantidade de parcelas com falha",
                    "schema": {"type": "integer", "example": 1}
                }
            }
        },
        400: {"description": "Parâmetros inválidos (nenhum código, mais de 50, ou tipo inválido)"},
        401: {"description": "Sessão expirada - necessário reautenticar"},
    },
)
async def download_lote_arquivos(
    codigos: str,
    _api_key: RequireAPIKey,
    tipos: str | None = None,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """
    Retorna ZIP com arquivos de múltiplas parcelas.
    
    Args:
        codigos: Códigos separados por vírgula
        tipos: Tipos separados por vírgula (parcela,vertice,limite)
    """
    try:
        # Parse dos parâmetros
        codigo_list = [c.strip() for c in codigos.split(",") if c.strip()]
        
        if not codigo_list:
            raise HTTPException(status_code=400, detail="Nenhum código fornecido")
        
        if len(codigo_list) > 50:
            raise HTTPException(status_code=400, detail="Máximo de 50 parcelas por requisição")
        
        # Parse dos tipos
        tipo_list = None
        if tipos:
            tipo_list = [TipoExportacao(t.strip().lower()) for t in tipos.split(",") if t.strip()]
        
        # Baixa todos
        results = await sigef_service.download_batch(
            codigos=codigo_list,
            tipos=tipo_list,
        )
        
        # Cria ZIP em memória
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for codigo, arquivos in results.items():
                if "error" in arquivos:
                    # Cria arquivo de erro para esta parcela
                    zip_file.writestr(
                        f"{codigo}/ERRO.txt",
                        f"Erro ao baixar parcela {codigo}: {arquivos['error']}"
                    )
                    continue
                
                for tipo, path_str in arquivos.items():
                    from pathlib import Path
                    path = Path(path_str)
                    if path.exists():
                        zip_file.write(path, f"{codigo}/{codigo}_{tipo}.csv")
        
        zip_buffer.seek(0)
        content = zip_buffer.read()
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="lote_{len(codigo_list)}_parcelas.zip"',
                "Content-Length": str(len(content)),
                "X-Filename": f"lote_{len(codigo_list)}_parcelas.zip",
                "X-Total-Parcelas": str(len(codigo_list)),
                "X-Sucesso": str(sum(1 for r in results.values() if "error" not in r)),
                "X-Falhas": str(sum(1 for r in results.values() if "error" in r)),
            },
        )
        
    except SessionExpiredError as e:
        raise HTTPException(status_code=401, detail=str(e))
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Tipo inválido: {e}")
        
    except Exception as e:
        logger.exception("Erro no download em lote")
        raise HTTPException(status_code=500, detail=str(e))
