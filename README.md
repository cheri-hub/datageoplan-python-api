# DataGeoPlan Python API

API unificada para integração com sistemas de dados geoespaciais brasileiros.

## 🎯 Plataformas Suportadas

| Plataforma | Status | Descrição |
|------------|--------|-----------|
| **SIGEF** | ✅ Ativo | Sistema de Gestão Fundiária (INCRA) |
| **SICAR** | ✅ Ativo | Sistema de Cadastro Ambiental Rural |

## 📡 Endpoints Disponíveis

### Autenticação (`/api/v1/auth`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/status` | Verifica status de autenticação |
| `POST` | `/browser-login` | Inicia fluxo de autenticação Gov.br |
| `POST` | `/browser-callback` | Recebe dados de autenticação |
| `POST` | `/logout` | Encerra sessão |

### SIGEF (`/api/v1/sigef`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/arquivo/csv/{codigo}/{tipo}` | Download CSV (parcela/vertice/limite) |
| `GET` | `/arquivo/todos/{codigo}` | Download ZIP com todos os arquivos |

### SICAR (`/api/v1/sicar`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/stream/state` | Download shapefile por estado |
| `POST` | `/stream/car` | Download shapefile por número CAR |
| `GET` | `/info` | Informações dos endpoints SICAR |

---

## 🚀 Deploy com Docker

### 1. Clone o Repositório

```bash
git clone https://github.com/cheri-hub/datageoplan-python-api.git
cd datageoplan-python-api
```

### 2. Build da Imagem

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
curl -X GET "http://localhost:8001/api/v1/sigef/arquivo/csv/999a354b/parcela" \
  -H "X-API-Key: sua-api-key" \
  -o parcela.csv
```

### SICAR - Download por Estado

```bash
curl -X POST "http://localhost:8001/api/v1/sicar/stream/state" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"state": "SP", "polygon": "AREA_PROPERTY"}' \
  -o SP_AREA_PROPERTY.zip
```

### SICAR - Download por CAR

```bash
curl -X POST "http://localhost:8001/api/v1/sicar/stream/car" \
  -H "X-API-Key: sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{"car_number": "SP-3538709-4861E981046E49BC81720C879459E554"}' \
  -o propriedade.zip
```

---

## ⚠️ Notas Importantes

### SICAR
- Downloads podem demorar **10-60 segundos** devido à resolução de captcha
- Configure timeout de **2 minutos** no cliente
- Tesseract OCR já está incluído na imagem Docker

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
