````instructions
# Copilot Instructions — DataGeoPlan Python API

## Contexto do Projeto
API REST em Python com FastAPI para integração com sistemas de dados geoespaciais brasileiros (SIGEF/INCRA e SICAR).
A aplicação segue Clean Architecture, Clean Code e SOLID, com foco em automação de browser (Playwright),
processamento GIS (GeoPandas) e autenticação Gov.br via certificado digital.

## Stack Tecnológica
- **Python 3.11+** | **FastAPI 0.104+** | **Pydantic v2** + **pydantic-settings**
- **Playwright** (automação Gov.br/SIGEF via Chrome do sistema)
- **httpx** + **requests** + **BeautifulSoup4** (clientes HTTP e parsing)
- **GeoPandas** + **Shapely** + **Fiona** + **pyproj** (processamento GIS)
- **structlog** (logging estruturado — JSON em produção, console colorido em dev)
- **slowapi** (rate limiting) | **python-jose** (JWT) | **tenacity** (retry)
- **pytesseract** + **Pillow** + **OpenCV** (OCR para captcha do SICAR)
- **ReportLab** (geração de PDFs)
- **Docker** + **Docker Compose** (deploy on-premise)
- **pytest** + **pytest-asyncio** (testes) | **ruff** (lint/format) | **mypy** (type check)

## Arquitetura: Clean Architecture (4 camadas)

```
src/
├── api/            → Apresentação: Routes FastAPI, schemas Pydantic, middlewares, DI
├── services/       → Aplicação: Orquestração de lógica de negócio (use cases)
├── domain/         → Domínio: Entidades (dataclasses), enums, interfaces abstratas (ABC/Protocol)
├── infrastructure/ → Infraestrutura: Implementações concretas (adapters)
│   ├── govbr/          → Autenticação Gov.br via Playwright
│   ├── sigef/          → Cliente HTTP para SIGEF/INCRA
│   ├── sicar_package/  → SICAR (captcha, download, processamento shapefiles, SLD)
│   ├── browser_auth/   → Fluxo de autenticação por browser remoto (Docker)
│   └── persistence/    → Repositório de sessões (JSON em disco)
└── core/           → Transversal: Config, exceptions, logging, segurança
```

### Regras de Dependência
- **Domain** → ZERO dependências externas. Apenas stdlib e abstrações.
- **Services** → Depende de Domain (interfaces). NUNCA importa Infrastructure diretamente.
- **Infrastructure** → Implementa interfaces de Domain. Pode usar libs externas.
- **API** → Thin layer. Monta Depends(), valida com Pydantic, despacha para Services.
- **Core** → Usado por todas as camadas (config, logging, exceptions).

## Entidades de Domínio

Todas em `src/domain/entities/`, implementadas como **dataclasses** (não Pydantic models):

| Entidade | Descrição |
|----------|-----------|
| `Session` | Sessão autenticada (cookies Gov.br/SIGEF/SICAR, JWT, expiration, flags de auth) |
| `JWTPayload` | Token Gov.br decodificado (CPF, nome, email, tokens, CNPJs) |
| `Parcela` | Parcela fundiária SIGEF (código, área, vértices, limites, centróide, situação) |
| `Vertice`, `Limite`, `Coordenada` | Componentes geométricos de uma parcela |
| `ParcelaSituacao` | Enum: `CERTIFICADA`, `PENDENTE`, `CANCELADA`, `EM_ANALISE` |
| `TipoExportacao` | Enum: `PARCELA`, `VERTICE`, `LIMITE` |

## Convenções de Código

### Idioma
- **Código** (variáveis, funções, classes): **português brasileiro** — consistente com os sistemas Gov.br integrados
- Exemplos: `processar_car()`, `baixar_shapefile()`, `sessao_expirada`, `ParcelaSituacao`
- Docstrings e comentários: português
- Logs: português com contexto estruturado

### Geral
- Type hints obrigatórios em toda função (parâmetros + retorno)
- Sintaxe moderna: `str | None`, `list[str]`, `dict[str, Any]` (não `Optional`, `List`, `Dict`)
- Funções: máximo ~20 linhas. Extrair se maior.
- Nomes snake_case descritivos: `baixar_csv_parcela()`, não `baixar()`
- PascalCase para classes: `SicarService`, `CarProcessor`
- UPPER_CASE para constantes: `MODELO_CAR`, `LAYER_MAPPING`, `UF_MAPPING`
- Sem magic numbers — usar constantes, `Enum` ou config
- Sem `print()` — usar `structlog` via `get_logger(__name__)`
- Sem `# type: ignore` sem justificativa
- Sem `Any` desnecessário — tipar explicitamente sempre que possível
- Todo package tem `__init__.py` com exports explícitos (`__all__`)

### FastAPI / Endpoints
- Schemas de request/response: **Pydantic BaseModel** (nunca `dict` bruto)
- Entidades de domínio: **dataclasses** (não Pydantic — separação de camadas)
- Status codes corretos: 200 (sucesso), 400 (validação), 401 (auth), 404 (não encontrado), 502 (erro de integração)
- File downloads: sempre via `StreamingResponse` com `media_type` e `Content-Disposition` corretos
- Dependency Injection via `Depends()` com factories `@lru_cache` em `dependencies.py`
- Versionamento em `/api/v1/`
- Paths públicos sem API key: `/health`, `/docs`, `/redoc`, `/openapi.json`, `/`

### Async e Threading
- Todo I/O de rede é async/await (httpx, FastAPI)
- **Exceção importante**: Playwright usa API **síncrona** rodando em `ThreadPoolExecutor`
  - Motivo: compatibilidade com `ProactorEventLoop` do Windows
  - Pattern: `await asyncio.get_event_loop().run_in_executor(None, sync_function)`
- Nunca bloquear event loop com operações sync de I/O
- `asynccontextmanager` para lifespan do app

### Autenticação (dois níveis)
1. **API Key** (stateless): Header `X-API-Key` ou `Authorization: Bearer <key>`
   - Middleware global `APIKeyMiddleware` + dependency `verify_api_key`
   - `secrets.compare_digest()` para comparação constant-time
   - Desabilitado em dev (warn no log)
2. **Sessão Gov.br** (stateful): Login com certificado digital via Playwright
   - Sessões salvas como JSON em disco (`data/sessions/session_{uuid}.json`)
   - Expiração: 12 horas
   - Flags por plataforma: `is_govbr_authenticated`, `is_sigef_authenticated`
   - Fluxo browser-auth para Docker: token temporário (10min) + callback

### Tratamento de Erros
Hierarquia de exceções customizadas em `src/core/exceptions.py`:

```
GovAuthException (base — code + details)
├── AuthenticationError
│   ├── SessionExpiredError
│   ├── SessionNotFoundError
│   └── CertificateError
├── IntegrationError (com service_name)
│   ├── GovBrError
│   └── SigefError
│       └── ParcelaNotFoundError
└── ValidationError
    └── InvalidParcelaCodeError
```

- Nunca `raise Exception("...")` genérica — sempre exceção customizada de domínio
- Global exception handler no `create_app()` converte para JSON estruturado
- Nunca expor stack traces em respostas HTTP
- Erro de captcha SICAR: retry loop (até 25 tentativas) antes de falhar

### Logging
- `structlog` com contexto estruturado: `logger.info("mensagem", session_id=..., cpf_masked=...)`
- Inicializar com `get_logger(__name__)` no topo do módulo
- **LGPD**: CPF e CNPJ mascarados via `src/core/security.py` (nunca logar dados sensíveis em claro)
- Formato: JSON em produção, console colorido em desenvolvimento
- Libs externas (httpx, playwright, urllib3) com nível WARNING para reduzir ruído

### Configuração
- `pydantic-settings` BaseSettings com suporte a `.env`
- Singleton via `@lru_cache` (`get_settings()`)
- Validação de API key em produção (rejeita keys fracas)
- CORS: wildcard bloqueado em produção
- Paths derivados: `data_dir`, `sessions_dir`, `downloads_dir`, `logs_dir`

### Processamento GIS / SICAR
- Processamento in-memory com GeoPandas (não salva arquivos temporários em disco quando possível)
- Temas CAR mapeados em `MODELO_CAR` (car_reference.py): 50+ temas em 7 grupos
- SLD (Styled Layer Descriptor): XML OGC 1.1.0 gerado programaticamente, compatível QGIS/GeoServer
- Cores padronizadas por tema: APP (amarelo), Reserva Legal (verde), etc.
- Shapefiles organizados por pasta temática no ZIP de saída

### Padrões Recorrentes

**Singleton com @lru_cache para DI:**
```python
@lru_cache
def get_sicar_service() -> SicarService:
    return SicarService(driver=get_settings().sicar_driver)
```

**Streaming de arquivos:**
```python
return StreamingResponse(
    iter([conteudo_bytes]),
    media_type="application/zip",
    headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
)
```

**Auto-reautenticação em services:**
```python
async def _execute_with_reauth(self, operation, *args, **kwargs):
    """Executa operação, reautentica automaticamente se sessão expirou."""
    try:
        return await operation(*args, **kwargs)
    except SessionExpiredError:
        await self._reautenticar()
        return await operation(*args, **kwargs)
```

**Retry com captcha (SICAR):**
```python
for tentativa in range(max_retries):
    try:
        resultado = await self._baixar_com_captcha(params)
        break
    except CaptchaError:
        logger.warning("Captcha falhou", tentativa=tentativa)
        continue
```

**Playwright sync em ThreadPoolExecutor:**
```python
loop = asyncio.get_event_loop()
resultado = await loop.run_in_executor(None, self._operacao_sync_playwright)
```

## Estrutura de Arquivos para Novos Endpoints

Ao criar um novo endpoint, seguir esta sequência:

1. **Domain**: Criar entidades/enums em `src/domain/entities/` e interfaces em `src/domain/interfaces/`
2. **Infrastructure**: Implementar adaptadores em `src/infrastructure/`
3. **Service**: Criar service em `src/services/` orquestrando domain + infrastructure
4. **Schema**: Criar request/response models em `src/api/v1/schemas.py`
5. **Route**: Criar arquivo em `src/api/v1/routes/` com `APIRouter`
6. **Dependencies**: Registrar factory com `@lru_cache` em `src/api/v1/dependencies.py`
7. **Router**: Incluir sub-router no `src/api/v1/__init__.py`

## Infraestrutura & Deploy

### Docker

**Dockerfile** — Imagem baseada em `python:3.11-slim`:
- Dependências de sistema: Playwright (libs Chromium), Tesseract OCR, GDAL/GEOS/PROJ (GIS)
- `playwright install chromium --with-deps` para browser headless
- Usuário não-root `appuser` (segurança)
- Healthcheck via `curl http://localhost:${PORT}/health`
- CMD: `uvicorn src.main:app --host 0.0.0.0 --port ${PORT}`

**docker-compose.yml** (desenvolvimento):
- Build local do Dockerfile
- Port `8000:8000`
- Bind mounts `./data/` para persistência local
- API_KEY default insegura (aceitável em dev)
- Nginx opcional via profile `with-nginx`

**docker-compose.prod.yml** (produção na VPS):
- Usa imagem pré-buildada `datageoplan-python-api:latest`
- Port `8001:8000` (container interno na 8000, host expõe na 8001)
- Volumes absolutos em `/opt/datageoplan-python-api/data/`
- `API_KEY=${API_KEY}` lida do `.env` no servidor
- CORS: `https://cherihub.cloud,https://datageoplan.cherihub.cloud`
- Logging: `json-file` com rotação (`max-size: 10m`, `max-file: 3`)

### CI/CD — GitHub Actions

Workflow em `.github/workflows/deploy.yml`. Trigger: push na `main` ou manual.

**3 Jobs sequenciais:**

1. **test** — Instala deps + roda `pytest tests/`
2. **build** — Build Docker, push para GHCR (`ghcr.io/cheri-hub/datageoplan-python-api`), salva artifact tar.gz
3. **deploy** — SCP da imagem + compose para a VPS, `docker load`, `docker compose up -d`

**Secrets necessários no GitHub:**

| Secret | Descrição |
|--------|-----------|
| `VPS_HOST` | IP ou hostname do servidor (ex: `cherihub.cloud`) |
| `VPS_USER` | Usuário SSH (ex: `root` ou `deploy`) |
| `VPS_SSH_KEY` | Chave privada SSH para acesso à VPS |
| `GITHUB_TOKEN` | Automático — usado para push ao GHCR |

**Fluxo de deploy na VPS:**
```
GitHub Actions → Build imagem → SCP tar.gz para /tmp/ → docker load →
  docker compose down → docker compose --env-file .env up -d → health check
```

**Diretórios no servidor:**
```
/opt/datageoplan-python-api/
├── docker-compose.yml        # Copiado do repo (docker-compose.prod.yml)
├── .env                      # API_KEY e configs sensíveis (NÃO versionado)
└── data/
    ├── sessions/             # Sessões autenticadas (JSON)
    ├── downloads/            # Shapefiles temporários
    ├── logs/                 # Logs da aplicação
    └── browser_auth/         # Tokens temporários browser-auth
```

### VPS — Servidor de Produção

- **Domínio**: `cherihub.cloud` / `datageoplan.cherihub.cloud`
- **Nginx** externo (instalado na VPS, fora do Docker) como reverse proxy
- **Porta interna da API**: `8001` no host → `8000` no container
- **SSL**: Let's Encrypt (Certbot) gerenciado pelo Nginx da VPS
- `.env` no servidor: nunca sobrescrito pelo deploy — criado manualmente na primeira vez

**Configuração Nginx esperada na VPS** (não versionada no repo):
```nginx
server {
    listen 80;
    server_name datageoplan.cherihub.cloud;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name datageoplan.cherihub.cloud;

    ssl_certificate /etc/letsencrypt/live/datageoplan.cherihub.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/datageoplan.cherihub.cloud/privkey.pem;

    client_max_body_size 100M;   # Uploads de shapefiles grandes
    proxy_read_timeout 300s;     # SICAR pode demorar (captcha + download)
    proxy_connect_timeout 60s;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Variáveis de Ambiente

Configuração via `pydantic-settings` BaseSettings + `.env`:

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `ENVIRONMENT` | `development/staging/production` | `development` | Ambiente de execução |
| `DEBUG` | `bool` | `true` | Modo debug |
| `HOST` | `str` | `127.0.0.1` | Bind do servidor |
| `PORT` | `int` | `8000` | Porta interna |
| `API_KEY` | `str` | (inseguro) | **Obrigatório em produção** — mínimo 32 chars |
| `CORS_ORIGINS` | `str` | `localhost` | Origens CORS separadas por vírgula |
| `LOG_LEVEL` | `str` | `INFO` | Nível de log |
| `LOG_FORMAT` | `json/console` | `console` | Formato do log |
| `SICAR_DRIVER` | `str` | `tesseract` | OCR driver: `tesseract` ou `paddle` |
| `BROWSER_HEADLESS` | `bool` | `false` | Playwright headless mode |
| `BROWSER_TIMEOUT_MS` | `int` | `30000` | Timeout do browser |

**Regras de segurança em produção:**
- `API_KEY` com padrão inseguro (`dev-`, `change-`, `test-`) gera warning
- `API_KEY` < 32 caracteres gera warning
- `CORS_ORIGINS=*` proibido em produção (raise ValueError)
- Gerar chave forte: `openssl rand -hex 32`

## Comandos

```bash
# Desenvolvimento
uvicorn src.main:app --reload --port 8000

# Instalar Playwright browsers
playwright install chromium

# Docker (dev)
docker compose up -d                     # Subir (API + opcional Nginx)
docker compose down                      # Derrubar

# Docker (produção na VPS)
docker compose -f docker-compose.prod.yml up -d

# Testes
pytest                                   # Todos
pytest tests/unit                        # Unitários
pytest --cov=src --cov-report=html       # Coverage

# Lint e Formatação
ruff check .                             # Lint
ruff format .                            # Format
mypy src/                                # Type check

# Deploy manual (via workflow_dispatch)
# GitHub → Actions → Deploy to Production → Run workflow
```

## Não Fazer
- Não colocar lógica de negócio em routes — delegar para Services
- Não usar `import *`
- Não acessar infraestrutura diretamente nos Services — usar interfaces de Domain
- Não retornar dataclasses de domínio em respostas HTTP — usar schemas Pydantic
- Não usar `print()` — usar `structlog`
- Não hardcodar secrets — usar `pydantic-settings` / variáveis de ambiente
- Não logar CPF/CNPJ em claro — usar mascaramento LGPD
- Não usar `datetime.now()` sem timezone — usar `datetime.now(tz=...)` ou `datetime.utcnow()`
- Não criar Playwright contexts sem fechar (`browser.close()`) — evitar vazamento de processos
- Não ignorar captcha failures no SICAR — sempre implementar retry loop
- Não salvar dados sensíveis (cookies, tokens) nos logs
- Não misturar Playwright async com sync — manter sync API dentro de `run_in_executor`
- Não usar `FutureWarning`-prone syntax do GeoPandas — manter compatibilidade com versões recentes
````
