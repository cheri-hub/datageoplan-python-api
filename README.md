# DataGeoPlan Python API

API unificada para integração com sistemas de dados geoespaciais brasileiros.

## 🎯 Plataformas Suportadas

| Plataforma | Status | Descrição |
|------------|--------|-----------|
| **SIGEF** | ✅ Ativo | Sistema de Gestão Fundiária (INCRA) |
| **SICAR** | ✅ Ativo | Sistema de Cadastro Ambiental Rural |

## 📡 Endpoints Disponíveis

### Autenticação (`/api/auth`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/status` | Verifica status de autenticação |
| `POST` | `/browser-login` | Inicia fluxo de autenticação Gov.br |
| `POST` | `/browser-callback` | Recebe dados de autenticação |
| `POST` | `/logout` | Encerra sessão |

### SIGEF (`/api/sigef`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/arquivo/csv/{codigo}/{tipo}` | Download CSV (parcela/vertice/limite) |
| `GET` | `/arquivo/todos/{codigo}` | Download ZIP com todos os arquivos |

### SICAR (`/api/sicar`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/stream/state` | Download shapefile por estado |
| `POST` | `/stream/car` | Download shapefile por número CAR |
| `POST` | `/stream/state/processed` | Download shapefile processado por estado com SLD |
| `POST` | `/stream/car/processed` | Download shapefile de CAR processado com SLD |
| `GET` | `/temas` | Lista grupos de temas CAR disponíveis |
| `GET` | `/temas/{grupo}` | Lista temas de um grupo específico |
| `GET` | `/sld/{tema}` | Gera arquivo SLD para um tema |
| `GET` | `/cores` | Paleta de cores de todos os temas |
| `GET` | `/info` | Informações dos endpoints SICAR |

---

## 🗺️ Processamento CAR - O que é e para que serve?

### O Problema

Quando você baixa dados do SICAR (Sistema de Cadastro Ambiental Rural), recebe um **ZIP bagunçado** contendo vários shapefiles misturados, sem organização e sem estilos visuais. Para usar no QGIS ou GeoServer, você precisa:

1. Extrair manualmente os arquivos
2. Identificar o que cada shapefile representa
3. Configurar cores e estilos para cada camada
4. Organizar em pastas por tema

### A Solução

Os novos endpoints **`/processed`** fazem todo esse trabalho automaticamente:

```
ZIP do SICAR (bagunçado) → API processa → ZIP organizado com estilos SLD
```

### O que você recebe no ZIP processado:

```
CAR_Processado_SP-123456/
├── Area_do_Imovel/
│   ├── Area_do_Imovel.shp        # Shapefile
│   ├── Area_do_Imovel.sld        # Estilo (cor amarela, sem preenchimento)
│   └── Sede_ou_Ponto_de_Referencia_do_Imovel.shp
│
├── Area_de_Preservacao_Permanente/
│   ├── APP_Rios_ate_10_metros.shp
│   ├── APP_Rios_ate_10_metros.sld
│   ├── Nascente_ou_Olho_dagua_Perene.shp
│   └── ...
│
├── Reserva_Legal/
│   ├── Reserva_Legal_Proposta.shp
│   ├── Reserva_Legal_Proposta.sld  # Estilo verde escuro
│   └── ...
│
└── Cobertura_do_Solo/
    ├── Area_Consolidada.shp
    ├── Remanescente_de_Vegetacao_Nativa.shp
    └── ...
```

### Arquivos SLD - O que são?

**SLD (Styled Layer Descriptor)** são arquivos XML que definem como visualizar cada camada:

- **Cores padronizadas** - APP em amarelo, Reserva Legal em verde, etc.
- **Compatíveis com QGIS** - Importe direto e as cores já aparecem
- **Compatíveis com GeoServer** - Publique camadas já estilizadas

### Endpoints de Consulta

| Endpoint | Para que serve |
|----------|----------------|
| `GET /temas` | Ver todos os grupos temáticos disponíveis |
| `GET /temas/{grupo}` | Ver temas de um grupo (ex: todas as APPs) |
| `GET /sld/{tema}` | Baixar apenas o arquivo SLD de um tema |
| `GET /cores` | Obter a paleta de cores (útil para legendas) |

### Exemplo Prático

**Sem processamento:**
```bash
# Baixa ZIP bruto do SICAR - você terá que organizar manualmente
curl -X POST ".../sicar/stream/car" -d '{"car_number": "SP-123"}' -o bruto.zip
```

**Com processamento:**
```bash
# Baixa ZIP já organizado com pastas e estilos SLD prontos
curl -X POST ".../sicar/stream/car/processed" -d '{"car_number": "SP-123"}' -o processado.zip
```

### Fluxo de Uso no QGIS

1. Baixe o ZIP processado via API
2. Extraia em uma pasta
3. Arraste os `.shp` para o QGIS
4. Clique com botão direito na camada → Estilos → Carregar Estilo → selecione o `.sld`
5. As cores padrão do CAR já estarão aplicadas

---

## � Desenvolvimento Local

### Pré-requisitos

- Python 3.11+
- Tesseract OCR (para SICAR)
- GDAL (para processamento GIS)

**Windows:**
```powershell
# Instalar Tesseract OCR
winget install UB-Mannheim.TesseractOCR

# GDAL - instalar via OSGeo4W ou conda
conda install -c conda-forge gdal geopandas
```

**Linux/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-por libgdal-dev gdal-bin python3-gdal
```

### 1. Clone e Configure

```bash
git clone https://github.com/cheri-hub/datageoplan-python-api.git
cd datageoplan-python-api

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente (Windows)
.venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source .venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt

# Instalar browsers do Playwright (para SIGEF)
playwright install chromium
```

### 3. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o `.env`:
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
API_KEY=dev-key-apenas-para-desenvolvimento
```

### 4. Executar

```bash
# Opção 1: Uvicorn direto
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Opção 2: Via Python
python -m uvicorn src.main:app --reload --port 8000
```

Acesse:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## �🚀 Deploy com Docker

### 🐳 Imagem Docker

A imagem está disponível no GitHub Container Registry:

```bash
docker pull ghcr.io/cheri-hub/datageoplan-python-api:latest
```

### 1. Clone o Repositório (opcional - só se for fazer build local)

```bash
git clone https://github.com/cheri-hub/datageoplan-python-api.git
cd datageoplan-python-api
```

### 2. Build da Imagem (opcional)

```bash
docker build -t datageoplan-python-api:latest .
```

### 3. Configuração

Crie o arquivo `.env`:

```bash
cp .env.example .env
```

Edite o `.env` com suas configurações:

```env
# ============== Ambiente ==============
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# ============== Servidor ==============
HOST=0.0.0.0
PORT=8000

# ============== Segurança ==============
# API Key (OBRIGATÓRIO - mínimo 32 caracteres)
# Gerar: openssl rand -base64 32
API_KEY=sua-chave-segura-aqui-minimo-32-chars

# ============== SICAR ==============
# Driver OCR: tesseract (padrão) ou paddle
SICAR_DRIVER=tesseract
```

### 4. Executar Container

**Opção A - Docker Run:**

```bash
docker run -d \
  --name datageoplan-python-api \
  --restart unless-stopped \
  -p 8001:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  datageoplan-python-api:latest
```

**Opção B - Docker Compose (recomendado):**

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 5. Verificar

```bash
# Status do container
docker ps | grep datageoplan

# Logs
docker logs datageoplan-python-api -f

# Health check
curl http://localhost:8001/health
```

---

## 🔐 Autenticação

Todas as requisições requerem API Key no header:

```
X-API-Key: sua-api-key
```

---

## 📋 Exemplos de Uso

### Health Check

```bash
curl http://localhost:8001/health
```

### SIGEF - Download CSV

```bash
curl -X GET "http://localhost:8001/api/sigef/arquivo/csv/999a354b/parcela" \
  -H "X-API-Key: sua-api-key" \
  -o parcela.csv
```

### SICAR - Download por Estado

```bash
curl -X POST "http://localhost:8001/api/sicar/stream/state" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"state": "SP", "polygon": "AREA_PROPERTY"}' \
  -o SP_AREA_PROPERTY.zip
```

### SICAR - Download por CAR

```bash
curl -X POST "http://localhost:8001/api/sicar/stream/car" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"car_number": "SP-3538709-4861E981046E49BC81720C879459E554"}' \
  -o propriedade.zip
```

### SICAR - Download Processado (com SLD)

```bash
# Download processado por estado (organizado por temas + arquivos SLD)
curl -X POST "http://localhost:8001/api/sicar/stream/state/processed" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"state": "SP", "polygon": "AREA_PROPERTY", "include_sld": true}' \
  -o SP_processado.zip

# Download de CAR processado
curl -X POST "http://localhost:8001/api/sicar/stream/car/processed" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"car_number": "SP-3538709-XXX", "include_sld": true}' \
  -o car_processado.zip
```

### SICAR - Consultar Temas e Estilos

```bash
# Listar grupos de temas CAR
curl "http://localhost:8001/api/sicar/temas" \
  -H "X-API-Key: sua-api-key"

# Listar temas de um grupo específico
curl "http://localhost:8001/api/sicar/temas/Area_de_Preservacao_Permanente" \
  -H "X-API-Key: sua-api-key"

# Obter SLD de um tema
curl "http://localhost:8001/api/sicar/sld/Area_do_Imovel" \
  -H "X-API-Key: sua-api-key" \
  -o area_imovel.sld

# Obter paleta de cores
curl "http://localhost:8001/api/sicar/cores" \
  -H "X-API-Key: sua-api-key"
```

---

## ⚠️ Notas Importantes

### SICAR
- Downloads podem demorar **10-60 segundos** devido à resolução de captcha
- Configure timeout de **2 minutos** no cliente (5-10 min para endpoints `/processed`)
- Tesseract OCR já está incluído na imagem Docker
- Endpoints `/processed` incluem:
  - Organização por grupos temáticos (APP, Reserva Legal, etc.)
  - Arquivos SLD para estilização em QGIS/GeoServer
  - Padronização de nomes e estrutura

### SIGEF
- Requer autenticação Gov.br via certificado digital
- Use o fluxo `browser-login` → `browser-callback`

### Portas
- Container interno: `8000`
- Porta externa padrão: `8001`

---

## 📚 Documentação

Acesse `/docs` para a documentação Swagger interativa:

```
http://localhost:8001/docs
```

---

## 📄 Licença

MIT
