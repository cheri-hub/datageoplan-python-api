# Gov.br Auth API

API enterprise para autenticação Gov.br via certificado digital A1 e integração com SIGEF INCRA.

## 🎯 Funcionalidades

- **Autenticação Gov.br**: Login via certificado digital A1
- **Integração SIGEF**: Acesso autenticado ao SIGEF INCRA
- **Download de CSVs**: Exportação de Parcela, Vértice e Limites
- **Download de Memorial Descritivo**: Exportação do memorial em PDF
- **Batch Processing**: Download em lote de múltiplas parcelas
- **API REST**: Endpoints documentados com Swagger/OpenAPI

## 📁 Estrutura do Projeto

```
gov-auth/
├── src/                        # Código fonte principal
│   ├── api/                    # Camada de Apresentação
│   │   └── v1/                 # API versão 1
│   │       ├── routes/         # Endpoints REST
│   │       │   ├── auth.py     # Autenticação
│   │       │   └── sigef.py    # Operações SIGEF
│   │       ├── schemas.py      # DTOs Pydantic
│   │       └── dependencies.py # Injeção de dependências
│   ├── core/                   # Configuração central
│   │   ├── config.py           # Settings (Pydantic)
│   │   ├── exceptions.py       # Exceções customizadas
│   │   └── logging.py          # Logging estruturado
│   ├── domain/                 # Camada de Domínio
│   │   ├── entities/           # Entidades (Session, Parcela)
│   │   └── interfaces/         # Contratos/Abstrações
│   ├── infrastructure/         # Camada de Infraestrutura
│   │   ├── govbr/              # Cliente Gov.br (Playwright)
│   │   ├── sigef/              # Cliente SIGEF (httpx)
│   │   └── persistence/        # Repositório de sessões
│   ├── services/               # Camada de Aplicação
│   │   ├── auth_service.py     # Orquestração de auth
│   │   └── sigef_service.py    # Operações SIGEF
│   └── main.py                 # FastAPI app
├── tests/                      # Testes automatizados
│   ├── conftest.py             # Fixtures compartilhadas
│   ├── test_api.py             # Testes de API
│   └── test_domain.py          # Testes de domínio
├── legacy/                     # Scripts originais (exploratório)
│   ├── gravar_chrome_sistema.py
│   ├── acessar_sigef.py
│   ├── sigef_api_direta.py
│   └── sigef_mapear_apis.py
├── _DOCS/                      # Documentação técnica
│   ├── 01_login_govbr.md
│   ├── 02_autenticacao_sigef.md
│   └── 03_download_csv_sigef.md
├── cli.py                      # Interface de linha de comando
├── Dockerfile                  # Container Docker
├── docker-compose.yml          # Orquestração Docker
├── requirements.txt            # Dependências Python
├── pyproject.toml              # Configuração do projeto
├── .env.example                # Exemplo de variáveis
└── README.md
```

## 🏗️ Princípios SOLID

| Princípio | Aplicação |
|-----------|-----------|
| **S**ingle Responsibility | Cada classe tem uma única responsabilidade |
| **O**pen/Closed | Extensível via interfaces, fechado para modificação |
| **L**iskov Substitution | Implementações substituíveis via interfaces |
| **I**nterface Segregation | Interfaces específicas (IGovBrAuthenticator, ISigefClient) |
| **D**ependency Inversion | Injeção de dependências via abstrações |

## 🚀 Quick Start

### Requisitos

- Python 3.11+
- Google Chrome instalado (para autenticação com certificado)
- Certificado digital A1 instalado no Windows

### Instalação

```bash
# Clone o repositório
git clone https://github.com/example/gov-auth.git
cd gov-auth

# Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Instale browsers do Playwright
playwright install chrome
```

### Configuração

```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite as configurações
notepad .env
```

### Execução

```bash
# Desenvolvimento
python -m src.main

# Ou com uvicorn
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Acesse: http://localhost:8000/docs

## 📡 API Endpoints

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/auth/status` | Verifica status da sessão |
| POST | `/api/v1/auth/login` | Inicia autenticação Gov.br |
| POST | `/api/v1/auth/logout` | Encerra sessão |
| GET | `/api/v1/auth/session` | Detalhes da sessão |

### SIGEF

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/sigef/parcela/{codigo}` | Info da parcela |
| POST | `/api/v1/sigef/download` | Download de CSV |
| POST | `/api/v1/sigef/download/all` | Download de todos CSVs |
| POST | `/api/v1/sigef/download/batch` | Download em lote |
| GET | `/api/v1/sigef/download/{codigo}/{tipo}` | Download direto do arquivo || GET | `/api/v1/sigef/memorial/{codigo}` | Download do memorial descritivo (PDF) |
## 🐳 Docker

```bash
# Build
docker build -t gov-auth .

# Run
docker run -p 8000:8000 gov-auth

# Docker Compose
docker-compose up -d
```

## 🧪 Testes

O projeto inclui **18 testes automatizados** que rodam em ~0.2s sem necessidade de certificado digital.

```bash
# Executar todos os testes
pytest tests/ -v

# Com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/test_api.py -v
pytest tests/test_domain.py -v
```

### Estratégia de Testes

| Tipo | Descrição | Requer Certificado |
|------|-----------|-------------------|
| **Unitários** | Testam componentes isolados com mocks | ❌ Não |
| **Integração** | Testam fluxo real (manual) | ✅ Sim |

Os testes unitários usam **mocks** para simular serviços externos (Gov.br, SIGEF), permitindo:
- Execução rápida e determinística
- Sem dependência de rede ou certificado
- Validação de lógica de negócio isolada

## 📊 Qualidade de Código

```bash
# Formatação
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

## 🔧 Configuração

Variáveis de ambiente (`.env`):

| Variável | Descrição | Default |
|----------|-----------|---------|
| `ENVIRONMENT` | dev/staging/production | development |
| `DEBUG` | Modo debug | true |
| `LOG_LEVEL` | Nível de log | INFO |
| `HOST` | Host do servidor | 0.0.0.0 |
| `PORT` | Porta do servidor | 8000 |
| `CORS_ORIGINS` | Origens CORS | * |

## 📚 Documentação

- [Login Gov.br](_DOCS/01_login_govbr.md)
- [Autenticação SIGEF](_DOCS/02_autenticacao_sigef.md)
- [Download CSV](_DOCS/03_download_csv_sigef.md)
- [Memorial Descritivo PDF](_DOCS/04_memorial_descritivo.md)

## 🏢 Deploy On-Premise

### Com Gunicorn

```bash
gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### Com systemd

```ini
[Unit]
Description=Gov.br Auth API
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/opt/gov-auth
Environment="PATH=/opt/gov-auth/.venv/bin"
ExecStart=/opt/gov-auth/.venv/bin/gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📝 Licença

MIT License

## 📦 Scripts Legados

Scripts de desenvolvimento da fase exploratória estão em [legacy/](legacy/):

| Script | Descrição |
|--------|-----------|
| `gravar_chrome_sistema.py` | Login Gov.br via certificado A1 |
| `acessar_sigef.py` | Acesso autenticado ao SIGEF |
| `sigef_api_direta.py` | Downloads via HTTP direto |
| `sigef_mapear_apis.py` | Mapeamento de endpoints SIGEF |

Estes scripts foram refatorados para a arquitetura enterprise em `src/`.

---

*Desenvolvido com 🐍 Python + FastAPI*
