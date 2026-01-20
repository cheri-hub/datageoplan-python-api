# DataGeoPlan Python API

API unificada para integração com sistemas de dados geoespaciais brasileiros.

## 🎯 Plataformas Suportadas

| Plataforma | Status | Descrição |
|------------|--------|-----------|
| **SIGEF** | ✅ Ativo | Sistema de Gestão Fundiária (INCRA) |
| **SICAR** | ✅ Ativo | Sistema de Cadastro Ambiental Rural |

## 📡 Endpoints Disponíveis

### Autenticação (`/v1/auth`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/status` | Verifica status de autenticação |
| `POST` | `/browser-login` | Inicia fluxo de autenticação Gov.br |
| `POST` | `/browser-callback` | Recebe dados de autenticação |
| `POST` | `/logout` | Encerra sessão |

### SIGEF (`/v1/sigef`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/arquivo/csv/{codigo}/{tipo}` | Download CSV (parcela/vertice/limite) |
| `GET` | `/arquivo/todos/{codigo}` | Download ZIP com todos os arquivos |

### SICAR (`/v1/sicar`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/stream/state` | Download shapefile por estado |
| `POST` | `/stream/car` | Download shapefile por número CAR |
| `GET` | `/info` | Informações dos endpoints SICAR |

## 📁 Estrutura do Projeto

```
datageoplan-python-api/
├── src/
│   ├── api/
│   │   ├── middleware/          # Auth, Rate Limit, Security
│   │   └── v1/
│   │       └── routes/
│   │           ├── auth.py      # Endpoints de autenticação
│   │           ├── sigef.py     # Endpoints SIGEF
│   │           └── sicar.py     # Endpoints SICAR
│   ├── core/                    # Config, Logging, Exceptions
│   ├── domain/                  # Entidades
│   ├── infrastructure/
│   │   ├── govbr/               # Autenticador Gov.br
│   │   ├── sigef/               # Cliente SIGEF
│   │   └── sicar_package/       # Cliente SICAR
│   ├── services/                # Services layer
│   └── main.py                  # FastAPI app
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
└── .env.example
```

## 🚀 Quick Start

### Requisitos

- Python 3.11+
- Google Chrome (para SIGEF)
- Tesseract OCR (para SICAR)

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/cheri-hub/datageoplan-python-api.git
cd datageoplan-python-api

# Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Instale Playwright browsers (para SIGEF)
playwright install chromium
```

### Configuração

```bash
cp .env.example .env
```

Edite `.env`:

```env
API_KEY=sua-chave-segura-aqui
ENVIRONMENT=development
```

### Executar

```bash
# Desenvolvimento
python -m uvicorn src.main:app --reload --port 8000

# Produção
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build
docker build -t datageoplan-python-api .

# Run
docker run -p 8000:8000 \
  -e API_KEY=sua-chave \
  datageoplan-python-api

# Docker Compose
docker compose up -d
```

## 🔐 Autenticação

Todas as requisições requerem API Key no header:

```
X-API-Key: sua-api-key
```

## 📋 Exemplos de Uso

### SIGEF - Download CSV

```bash
curl -X GET "http://localhost:8000/api/v1/sigef/arquivo/csv/999a354b/parcela" \
  -H "X-API-Key: sua-api-key" \
  -o parcela.csv
```

### SICAR - Download por Estado

```bash
curl -X POST "http://localhost:8000/api/v1/sicar/stream/state" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"state": "SP", "polygon": "AREA_PROPERTY"}' \
  -o SP_AREA_PROPERTY.zip
```

### SICAR - Download por CAR

```bash
curl -X POST "http://localhost:8000/api/v1/sicar/stream/car" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"car_number": "SP-3538709-4861E981046E49BC81720C879459E554"}' \
  -o propriedade.zip
```

## ⚠️ Notas Importantes

### SICAR
- Downloads podem demorar **10-60 segundos** devido à resolução de captcha
- Configure timeout de **2 minutos** no cliente
- Requer Tesseract OCR instalado no servidor

### SIGEF
- Requer autenticação Gov.br via certificado digital
- Use o fluxo `browser-login` → `browser-callback`

## 📦 Clientes

- **C# Client**: https://github.com/cheri-hub/sigef-client

## 📚 Documentação

Acesse `/docs` para a documentação Swagger interativa.

## 📄 Licença

MIT
