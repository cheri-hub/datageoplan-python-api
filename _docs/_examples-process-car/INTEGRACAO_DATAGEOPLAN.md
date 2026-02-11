# Integração: Processador CAR + APIs DataGeoPlan

Análise de integração entre o processador CAR local (`process-car-api`) e as APIs de dados geoespaciais.

## Visão Geral - 3 Projetos

### 1. datageoplan-python-api (`C:\repo\datageoplan-python-api`)
API FastAPI para **SIGEF** (parcelas INCRA) com autenticação Gov.br.

**Endpoints:**
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/v1/auth/browser-login` | Login Gov.br via certificado |
| `GET` | `/v1/sigef/arquivo/csv/{codigo}/{tipo}` | Download CSV (parcela/vertice/limite) |
| `GET` | `/v1/sigef/arquivo/todos/{codigo}` | Download ZIP completo |

**Estrutura:**
```
src/
├── api/v1/routes/
│   ├── auth.py          # Autenticação Gov.br
│   └── sigef.py         # Endpoints SIGEF
├── services/
│   └── sigef_service.py
└── infrastructure/
    └── sigef/           # Cliente SIGEF
```

---

### 2. sicarAPI (`C:\repo\sicarAPI`)
API FastAPI para **SICAR** - Download de shapefiles do Cadastro Ambiental Rural.

**Endpoints:**
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/stream/state` | Download shapefile por estado |
| `POST` | `/stream/car` | Download shapefile por número CAR |
| `GET` | `/health` | Health check |

**Polígonos disponíveis:**
- `AREA_PROPERTY` - Área do Imóvel
- `APPS` - Áreas de Preservação Permanente
- `NATIVE_VEGETATION` - Vegetação Nativa
- `LEGAL_RESERVE` - Reserva Legal
- `RESTRICTED_USE` - Uso Restrito
- `CONSOLIDATED_AREA` - Área Consolidada
- etc.

**Estrutura:**
```
app/
├── main.py              # FastAPI app
├── config.py            # Configurações
├── auth.py              # API Key auth
└── services/
    └── sicar_service.py # Download via SICAR package
```

---

### 3. process-car-api (este workspace)
Scripts para **PROCESSAR** shapefiles CAR baixados.

**Arquivos:**
- `processar_car.py` - Processador de shapefiles CAR
- `modelo_car_referencia.py` - Dicionário de temas com cores/estilos

---

## Fluxo Atual vs. Proposta de Integração

### Fluxo Atual (Separado)
```
sicarAPI                    process-car-api
   │                              │
   ▼                              ▼
Download ZIP ────(manual)────► Processar localmente
do SICAR                       com processar_car.py
```

### Fluxo Proposto (Integrado)
```
sicarAPI (com processador integrado)
   │
   ├── POST /stream/state ────► ZIP bruto do SICAR
   │
   └── POST /stream/state/processed ────► ZIP processado com SLD
             │
             ├── Baixa do SICAR
             ├── Processa com car_processor
             └── Retorna shapefiles organizados + SLD
```

---

## Proposta: Novos Endpoints para sicarAPI

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/stream/state/processed` | Download + processamento por estado |
| `POST` | `/stream/car/processed` | Download + processamento por CAR |
| `GET` | `/temas` | Lista todos os temas CAR disponíveis |
| `GET` | `/temas/{grupo}` | Temas de um grupo específico |
| `GET` | `/sld/{tema}` | Gera SLD para um tema |
| `GET` | `/cores` | Paleta de cores por tema |

---

## Estrutura de Arquivos a Adicionar em sicarAPI

```
sicarAPI/
└── app/
    ├── services/
    │   ├── sicar_service.py        # Existente
    │   └── car_processor.py        # NOVO - Baseado em processar_car.py
    ├── models/
    │   └── car_reference.py        # NOVO - Baseado em modelo_car_referencia.py
    └── utils/
        └── sld_generator.py        # NOVO - Geração de SLD
```

---

## Mapeamento de Funções

### De `processar_car.py` para `car_processor.py`

| Função Original | Uso na API |
|-----------------|------------|
| `processar_car()` | Endpoint `POST /stream/*/processed` |
| `encontrar_shapefiles_car()` | Interno - validação de ZIP |
| `analisar_temas_presentes()` | Interno - análise de ZIP |
| `extrair_recibo_car()` | Retornar metadados do CAR |

### De `processar_car.py` para `sld_generator.py`

| Função Original | Uso na API |
|-----------------|------------|
| `criar_sld_polygon()` | Endpoint `GET /sld/{tema}` |
| `criar_sld_point()` | Endpoint `GET /sld/{tema}` |
| `hex_para_rgb()` | Função auxiliar |

### De `modelo_car_referencia.py` para `car_reference.py`

| Elemento Original | Uso na API |
|-------------------|------------|
| `MODELO_CAR` | Endpoint `GET /temas` |
| `buscar_tema()` | Resolução de cores/estilos |

---

## Schemas Pydantic Sugeridos

```python
# app/schemas.py (sicarAPI)

class TemaCAR(BaseModel):
    tema_car: str
    arquivo_modelo: str
    cor_preenchimento: str | None
    cor_contorno: str
    tipo: Literal["Polygon", "Point"]

class GrupoCAR(BaseModel):
    nome_grupo: str
    ordem: int
    temas: list[TemaCAR]

class ResultadoProcessamento(BaseModel):
    recibo: str
    temas_processados: int
    feicoes_total: int
    arquivos_gerados: list[str]
    erros: list[str] | None = None

class ProcessedStateRequest(BaseModel):
    state: str
    polygon: str
    include_sld: bool = True

class ProcessedCARRequest(BaseModel):
    car_number: str
    include_sld: bool = True
```

---

## Exemplo de Uso da API Integrada

```bash
# sicarAPI (porta 8000)

# 1. Download bruto por estado (existente)
curl -X POST http://localhost:8000/stream/state \
  -H "X-API-Key: {api-key}" \
  -H "Content-Type: application/json" \
  -d '{"state": "SP", "polygon": "AREA_PROPERTY"}' \
  -o SP_bruto.zip

# 2. Download PROCESSADO por estado (NOVO)
curl -X POST http://localhost:8000/stream/state/processed \
  -H "X-API-Key: {api-key}" \
  -H "Content-Type: application/json" \
  -d '{"state": "SP", "polygon": "AREA_PROPERTY"}' \
  -o SP_processado.zip

# 3. Download PROCESSADO por CAR (NOVO)
curl -X POST http://localhost:8000/stream/car/processed \
  -H "X-API-Key: {api-key}" \
  -H "Content-Type: application/json" \
  -d '{"car_number": "SP-3538709-XXX"}' \
  -o car_processado.zip

# 4. Listar temas disponíveis (NOVO)
curl http://localhost:8000/temas \
  -H "X-API-Key: {api-key}"

# 5. Obter SLD de um tema específico (NOVO)
curl http://localhost:8000/sld/Area_do_Imovel \
  -H "X-API-Key: {api-key}" \
  -o area_imovel.sld

# 6. Obter paleta de cores (NOVO)
curl http://localhost:8000/cores \
  -H "X-API-Key: {api-key}"
```

---

## Dependências Adicionais

```txt
# sicarAPI/requirements.txt (adicionar)
geopandas>=0.14.0
shapely>=2.0.0
```

---

## Próximos Passos

1. [ ] Copiar `processar_car.py` para `sicarAPI/app/services/car_processor.py`
2. [ ] Copiar `modelo_car_referencia.py` para `sicarAPI/app/models/car_reference.py`
3. [ ] Criar `sicarAPI/app/utils/sld_generator.py`
4. [ ] Adicionar endpoints em `sicarAPI/app/main.py`:
   - `POST /stream/state/processed`
   - `POST /stream/car/processed`
   - `GET /temas`
   - `GET /sld/{tema}`
5. [ ] Adicionar schemas Pydantic
6. [ ] Atualizar Dockerfile com dependências geopandas
7. [ ] Adicionar testes
8. [ ] Documentar no Swagger

---

## Considerações

### Processamento em Memória
Para evitar I/O em disco:
1. sicarAPI baixa ZIP para bytes
2. car_processor processa em memória (BytesIO)
3. Retorna ZIP processado como stream

### Dependências Extras no Docker
```dockerfile
# sicarAPI/Dockerfile (adicionar)
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    python3-gdal
```

### Autenticação
Usar mesma estrutura de API Key (`X-API-Key`) já implementada.

---

## Resumo das APIs

| API | Porta | Função |
|-----|-------|--------|
| **datageoplan-python-api** | 8001 | SIGEF - Parcelas INCRA com auth Gov.br |
| **sicarAPI** | 8000 | SICAR - Download e processamento de CAR |
