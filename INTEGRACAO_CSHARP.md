# Integração C# com Gov.br Auth API

## Configuração da API

### 1. Variáveis de Ambiente (Production)

```bash
# .env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# Servidor
HOST=0.0.0.0
PORT=8000

# CORS - Adicione o domínio da aplicação C#
CORS_ORIGINS=https://seu-dominio.com.br,https://app.exemplo.com.br

# Segurança - OBRIGATÓRIO MUDAR
API_KEY=gere-uma-chave-forte-aqui-min-32-chars
SECRET_KEY=gere-outro-segredo-forte-aqui-min-32-chars
```

**Gerar chaves seguras:**
```bash
# Linux/Mac
openssl rand -hex 32

# PowerShell Windows
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 2. Deploy Docker

```bash
# Build
docker-compose build

# Run em produção
ENVIRONMENT=production docker-compose up -d

# Verificar logs
docker-compose logs -f api

# Health check
curl http://localhost:8000/health
```

---

## Cliente C# (.NET 6+)

### Instalação de Pacotes

```bash
dotnet add package System.Net.Http.Json
dotnet add package Microsoft.Extensions.Http
```

### Cliente HTTP Base

```csharp
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;

namespace GovAuth.Client
{
    public class GovAuthApiClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _apiKey;
        private readonly JsonSerializerOptions _jsonOptions;

        public GovAuthApiClient(string baseUrl, string apiKey)
        {
            _apiKey = apiKey;
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = TimeSpan.FromSeconds(60)
            };
            
            // Configura autenticação Bearer
            _httpClient.DefaultRequestHeaders.Authorization = 
                new AuthenticationHeaderValue("Bearer", apiKey);
            
            // Configura JSON (snake_case)
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
                PropertyNameCaseInsensitive = true
            };
        }

        /// <summary>
        /// Health check da API
        /// </summary>
        public async Task<bool> IsHealthyAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Faz login no Gov.br com certificado A1
        /// </summary>
        public async Task<LoginResponse> LoginAsync(string pfxPath, string password)
        {
            var request = new LoginRequest
            {
                CertificatePath = pfxPath,
                Password = password
            };

            var response = await _httpClient.PostAsJsonAsync(
                "/api/v1/auth/login", 
                request,
                _jsonOptions
            );

            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<LoginResponse>(_jsonOptions);
        }

        /// <summary>
        /// Verifica status da autenticação
        /// </summary>
        public async Task<AuthStatusResponse> GetAuthStatusAsync(string sessionId)
        {
            var response = await _httpClient.GetAsync($"/api/v1/auth/status/{sessionId}");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<AuthStatusResponse>(_jsonOptions);
        }

        /// <summary>
        /// Consulta imóveis por bounding box
        /// </summary>
        public async Task<ConsultaResponse> ConsultarImoveis(ConsultaRequest request)
        {
            var response = await _httpClient.PostAsJsonAsync(
                "/api/v1/consulta",
                request,
                _jsonOptions
            );

            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<ConsultaResponse>(_jsonOptions);
        }

        /// <summary>
        /// Busca detalhes de parcela SIGEF
        /// </summary>
        public async Task<ParcelaDetalhesResponse> GetParcelaDetalhesAsync(
            string sessionId, 
            string codigo
        )
        {
            var response = await _httpClient.GetAsync(
                $"/api/v1/sigef/detalhes/{codigo}?session_id={sessionId}"
            );

            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<ParcelaDetalhesResponse>(_jsonOptions);
        }

        /// <summary>
        /// Download de CSV (Parcela, Vértices, Limites)
        /// </summary>
        public async Task<byte[]> DownloadCsvAsync(
            string sessionId,
            string codigo,
            string tipo = "parcela"
        )
        {
            var request = new DownloadRequest
            {
                SessionId = sessionId,
                Codigo = codigo,
                Tipo = tipo
            };

            var response = await _httpClient.PostAsJsonAsync(
                "/api/v1/sigef/download/csv",
                request
            );

            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsByteArrayAsync();
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }
}
```

### DTOs (Data Transfer Objects)

```csharp
namespace GovAuth.Client.Models
{
    public record LoginRequest
    {
        public string CertificatePath { get; init; }
        public string Password { get; init; }
    }

    public record LoginResponse
    {
        public string SessionId { get; init; }
        public string Status { get; init; }
        public string Message { get; init; }
        public DateTime Timestamp { get; init; }
    }

    public record AuthStatusResponse
    {
        public bool Authenticated { get; init; }
        public string Status { get; init; }
        public DateTime? LastActivity { get; init; }
        public int RemainingMinutes { get; init; }
    }

    public record ConsultaRequest
    {
        public double MinX { get; init; }
        public double MinY { get; init; }
        public double MaxX { get; init; }
        public double MaxY { get; init; }
        public string? Uf { get; init; }
    }

    public record ConsultaResponse
    {
        public int TotalFeatures { get; init; }
        public List<Feature> Features { get; init; }
        public Dictionary<string, int> ResultadosPorCamada { get; init; }
    }

    public record Feature
    {
        public string Camada { get; init; }
        public Dictionary<string, object> Properties { get; init; }
        public object Geometry { get; init; }
    }

    public record ParcelaDetalhesResponse
    {
        public Dictionary<string, string> InformacoesParcela { get; init; }
        public HistoricoInfo Historico { get; init; }
        public Dictionary<string, object> AreaGeorreferenciada { get; init; }
        public List<Dictionary<string, string>> Detentores { get; init; }
        public Dictionary<string, string> Registro { get; init; }
    }

    public record HistoricoInfo
    {
        public int Quantidade { get; init; }
        public List<Dictionary<string, string>> Requerimentos { get; init; }
    }

    public record DownloadRequest
    {
        public string SessionId { get; init; }
        public string Codigo { get; init; }
        public string Tipo { get; init; } // "parcela", "vertice", "limite"
    }
}
```

### Uso em Controller ASP.NET Core

```csharp
using GovAuth.Client;
using GovAuth.Client.Models;
using Microsoft.AspNetCore.Mvc;

namespace SuaApp.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ImoveisController : ControllerBase
    {
        private readonly GovAuthApiClient _govAuthClient;
        private readonly IConfiguration _configuration;

        public ImoveisController(IConfiguration configuration)
        {
            _configuration = configuration;
            
            var baseUrl = _configuration["GovAuth:BaseUrl"]; // http://localhost:8000
            var apiKey = _configuration["GovAuth:ApiKey"];
            
            _govAuthClient = new GovAuthApiClient(baseUrl, apiKey);
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login([FromBody] LoginDto dto)
        {
            try
            {
                var result = await _govAuthClient.LoginAsync(
                    dto.CertificatePath,
                    dto.Password
                );
                
                return Ok(result);
            }
            catch (HttpRequestException ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }

        [HttpPost("consultar")]
        public async Task<IActionResult> Consultar([FromBody] ConsultaDto dto)
        {
            try
            {
                var request = new ConsultaRequest
                {
                    MinX = dto.MinX,
                    MinY = dto.MinY,
                    MaxX = dto.MaxX,
                    MaxY = dto.MaxY,
                    Uf = dto.Uf
                };

                var result = await _govAuthClient.ConsultarImoveis(request);
                return Ok(result);
            }
            catch (HttpRequestException ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }

        [HttpGet("detalhes/{codigo}")]
        public async Task<IActionResult> GetDetalhes(string codigo, [FromQuery] string sessionId)
        {
            try
            {
                var result = await _govAuthClient.GetParcelaDetalhesAsync(sessionId, codigo);
                return Ok(result);
            }
            catch (HttpRequestException ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }

        [HttpPost("download-csv")]
        public async Task<IActionResult> DownloadCsv([FromBody] DownloadDto dto)
        {
            try
            {
                var csvBytes = await _govAuthClient.DownloadCsvAsync(
                    dto.SessionId,
                    dto.Codigo,
                    dto.Tipo
                );

                return File(csvBytes, "text/csv", $"{dto.Codigo}_{dto.Tipo}.csv");
            }
            catch (HttpRequestException ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }
    }
}
```

### appsettings.json

```json
{
  "GovAuth": {
    "BaseUrl": "http://localhost:8000",
    "ApiKey": "sua-api-key-aqui"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

---

## Endpoints de Download Direto (NOVO)

### Endpoints Disponíveis

| Endpoint | Método | Descrição | Retorno |
|----------|--------|-----------|---------|
| `/api/v1/sigef/arquivo/csv/{codigo}/{tipo}` | GET | Download CSV individual | `text/csv` |
| `/api/v1/sigef/arquivo/memorial/{codigo}` | GET | Download memorial PDF | `application/pdf` |
| `/api/v1/sigef/arquivo/todos/{codigo}` | GET | Download ZIP completo | `application/zip` |
| `/api/v1/sigef/arquivo/lote?codigos=...` | GET | Download em lote | `application/zip` |

### Tipos de CSV

- `parcela`: Dados gerais da parcela
- `vertice`: Coordenadas dos vértices
- `limite`: Limites da parcela

---

### Cliente C# para Download Direto

```csharp
using System.IO.Compression;

namespace GovAuth.Client
{
    public partial class GovAuthApiClient
    {
        /// <summary>
        /// Download direto de CSV
        /// </summary>
        public async Task<byte[]> DownloadCsvDiretoAsync(string codigo, string tipo)
        {
            var response = await _httpClient.GetAsync(
                $"/api/v1/sigef/arquivo/csv/{codigo}/{tipo}"
            );
            
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsByteArrayAsync();
        }

        /// <summary>
        /// Download direto de CSV e salva em arquivo
        /// </summary>
        public async Task<string> DownloadCsvParaArquivoAsync(
            string codigo, 
            string tipo, 
            string diretorioDestino)
        {
            var bytes = await DownloadCsvDiretoAsync(codigo, tipo);
            
            var nomeArquivo = $"{codigo}_{tipo}.csv";
            var caminhoCompleto = Path.Combine(diretorioDestino, nomeArquivo);
            
            await File.WriteAllBytesAsync(caminhoCompleto, bytes);
            return caminhoCompleto;
        }

        /// <summary>
        /// Download do memorial descritivo (PDF)
        /// </summary>
        public async Task<byte[]> DownloadMemorialAsync(string codigo)
        {
            var response = await _httpClient.GetAsync(
                $"/api/v1/sigef/arquivo/memorial/{codigo}"
            );
            
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsByteArrayAsync();
        }

        /// <summary>
        /// Download de todos os arquivos de uma parcela (ZIP)
        /// </summary>
        public async Task<byte[]> DownloadTodosArquivosAsync(string codigo)
        {
            var response = await _httpClient.GetAsync(
                $"/api/v1/sigef/arquivo/todos/{codigo}"
            );
            
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsByteArrayAsync();
        }

        /// <summary>
        /// Download e extração de todos os arquivos
        /// </summary>
        public async Task<string> DownloadEExtrairTodosAsync(
            string codigo, 
            string diretorioDestino)
        {
            var zipBytes = await DownloadTodosArquivosAsync(codigo);
            
            var pastaDestino = Path.Combine(diretorioDestino, codigo);
            Directory.CreateDirectory(pastaDestino);
            
            using (var zipStream = new MemoryStream(zipBytes))
            using (var archive = new ZipArchive(zipStream, ZipArchiveMode.Read))
            {
                archive.ExtractToDirectory(pastaDestino, overwriteFiles: true);
            }
            
            return pastaDestino;
        }

        /// <summary>
        /// Download em lote (múltiplas parcelas)
        /// </summary>
        public async Task<byte[]> DownloadLoteAsync(
            IEnumerable<string> codigos, 
            IEnumerable<string>? tipos = null)
        {
            var codigosParam = string.Join(",", codigos);
            var url = $"/api/v1/sigef/arquivo/lote?codigos={codigosParam}";
            
            if (tipos != null && tipos.Any())
            {
                url += $"&tipos={string.Join(",", tipos)}";
            }
            
            var response = await _httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadAsByteArrayAsync();
        }

        /// <summary>
        /// Download em lote e extração
        /// </summary>
        public async Task<string> DownloadLoteEExtrairAsync(
            IEnumerable<string> codigos,
            string diretorioDestino,
            IEnumerable<string>? tipos = null)
        {
            var zipBytes = await DownloadLoteAsync(codigos, tipos);
            
            var pastaDestino = Path.Combine(diretorioDestino, "lote_download");
            Directory.CreateDirectory(pastaDestino);
            
            using (var zipStream = new MemoryStream(zipBytes))
            using (var archive = new ZipArchive(zipStream, ZipArchiveMode.Read))
            {
                archive.ExtractToDirectory(pastaDestino, overwriteFiles: true);
            }
            
            return pastaDestino;
        }
    }
}
```

### Exemplo de Uso Completo

```csharp
// Configuração
var client = new GovAuthApiClient("http://localhost:8000", "sua-api-key");

// 1. Download de um CSV específico
var csvParcela = await client.DownloadCsvDiretoAsync(
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890", 
    "parcela"
);
File.WriteAllBytes("parcela.csv", csvParcela);

// 2. Download do memorial PDF
var memorial = await client.DownloadMemorialAsync(
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
);
File.WriteAllBytes("memorial.pdf", memorial);

// 3. Download de todos os arquivos em ZIP
var zipCompleto = await client.DownloadTodosArquivosAsync(
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
);
File.WriteAllBytes("parcela_completa.zip", zipCompleto);

// 4. Download em lote de múltiplas parcelas
var codigos = new[] {
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "c3d4e5f6-a7b8-9012-cdef-123456789012"
};

var loteZip = await client.DownloadLoteAsync(codigos);
File.WriteAllBytes("lote_parcelas.zip", loteZip);

// 5. Download e extração automática
var pastaExtraida = await client.DownloadLoteEExtrairAsync(
    codigos,
    @"C:\Downloads\Parcelas"
);
Console.WriteLine($"Arquivos extraídos em: {pastaExtraida}");
```

### Controller ASP.NET Core para Download

```csharp
[ApiController]
[Route("api/[controller]")]
public class DownloadsController : ControllerBase
{
    private readonly GovAuthApiClient _client;

    public DownloadsController(GovAuthApiClient client)
    {
        _client = client;
    }

    [HttpGet("csv/{codigo}/{tipo}")]
    public async Task<IActionResult> DownloadCsv(string codigo, string tipo)
    {
        var bytes = await _client.DownloadCsvDiretoAsync(codigo, tipo);
        return File(bytes, "text/csv", $"{codigo}_{tipo}.csv");
    }

    [HttpGet("memorial/{codigo}")]
    public async Task<IActionResult> DownloadMemorial(string codigo)
    {
        var bytes = await _client.DownloadMemorialAsync(codigo);
        return File(bytes, "application/pdf", $"{codigo}_memorial.pdf");
    }

    [HttpGet("completo/{codigo}")]
    public async Task<IActionResult> DownloadCompleto(string codigo)
    {
        var bytes = await _client.DownloadTodosArquivosAsync(codigo);
        return File(bytes, "application/zip", $"{codigo}_completo.zip");
    }

    [HttpPost("lote")]
    public async Task<IActionResult> DownloadLote([FromBody] string[] codigos)
    {
        var bytes = await _client.DownloadLoteAsync(codigos);
        return File(bytes, "application/zip", $"lote_{codigos.Length}_parcelas.zip");
    }
}
```

---

## Swagger/OpenAPI

A API expõe documentação OpenAPI em:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

Você pode usar ferramentas como **NSwag** ou **AutoRest** para gerar cliente C# automaticamente:

```bash
# Instalar NSwag
dotnet tool install -g NSwag.ConsoleCore

# Gerar cliente
nswag openapi2csclient /input:http://localhost:8000/openapi.json /output:GovAuthClient.cs
```

---

## Tratamento de Erros

```csharp
public async Task<T> ExecuteWithRetry<T>(Func<Task<T>> operation, int maxRetries = 3)
{
    for (int i = 0; i < maxRetries; i++)
    {
        try
        {
            return await operation();
        }
        catch (HttpRequestException ex) when (i < maxRetries - 1)
        {
            // Log e aguarda antes de retry
            await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, i))); // Exponential backoff
        }
    }
    
    throw new Exception("Failed after max retries");
}
```

---

## Checklist de Deploy

- [ ] Gerar API_KEY e SECRET_KEY fortes
- [ ] Configurar CORS com domínio da aplicação C#
- [ ] Definir ENVIRONMENT=production
- [ ] Desabilitar DEBUG=false
- [ ] Configurar volumes Docker para persistência
- [ ] Configurar logs estruturados (LOG_FORMAT=json)
- [ ] Implementar reverse proxy (Nginx) com SSL
- [ ] Monitorar endpoint /health
- [ ] Configurar timeout adequado no HttpClient C#
- [ ] Implementar retry logic com exponential backoff

---

## Observações de Segurança

1. **API Key via Environment:** Nunca commitar no código
2. **HTTPS obrigatório** em produção
3. **Rate limiting** recomendado (não implementado ainda)
4. **Log de auditoria** habilitado em JSON format
5. **Certificados A1:** Armazenar em local seguro com permissões restritas
