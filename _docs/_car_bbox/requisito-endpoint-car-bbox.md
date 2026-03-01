# Requisito: Endpoint de Consulta de CARs por BBox

## 1. Visão Geral

Criar um endpoint na API existente que, dado um **Bounding Box (BBox)** geográfico e a **UF**, retorne a lista de códigos CAR (Cadastro Ambiental Rural) dos imóveis rurais contidos naquela região.

Car API já existe e está em operação. Este requisito trata da adição de um novo endpoint.

---

## 2. Fonte de Dados

O dado é consumido do **WFS público** do GeoServer do SICAR:

| Item | Valor |
|---|---|
| URL base | `https://geoserver.car.gov.br/geoserver/sicar/wfs` |
| Protocolo | WFS 1.1.0 |
| Operação | `GetFeature` |
| Formato de saída | `application/json` (GeoJSON) |
| SRS | `EPSG:4674` (SIRGAS 2000) |
| Camadas | `sicar_imoveis_{uf}` (uma por estado, 27 no total) |

### 2.1 Limitações conhecidas do GeoServer

| Limitação | Impacto | Mitigação |
|---|---|---|
| `BBOX` e `CQL_FILTER` são mutuamente exclusivos | Não é possível filtrar por atributo (ex.: status) no servidor | Aplicar filtros de atributo **client-side** após o retorno do WFS |
| WAF (Dataprev) bloqueia `CQL_FILTER` isolado | Mesmo tentando embutir BBOX no CQL, o firewall rejeita | Usar apenas o parâmetro `BBOX` nativo do WFS |
| Sem paginação server-side confiável | `STARTINDEX` pode não funcionar consistentemente | Controlar via `MAXFEATURES` + paginação client-side |
| SSL requer `SECLEVEL=1` | Handshake falha com configuração padrão do Python | Configurar `ssl.create_default_context()` com `set_ciphers("DEFAULT@SECLEVEL=1")` |

---

## 3. Endpoint

### 3.1 Definição

| Item | Valor |
|---|---|
| **Método** | `POST` |
| **Path** | `/api/car/bbox` |
| **Content-Type** | `application/json` |
| **Response Content-Type** | `application/json` |

### 3.2 Por que POST e não GET?

O BBox possui 4 coordenadas + filtros opcionais. Um POST com body JSON é mais limpo e extensível do que query params com coordenadas numéricas.

---

## 4. Request

### 4.1 Modelo: `ConsultaCarBboxRequest`

```json
{
  "bbox": {
    "min_lon": -47.1,
    "min_lat": -23.6,
    "max_lon": -47.0,
    "max_lat": -23.5
  },
  "uf": "SP",
  "max_resultados": 50,
  "incluir_geometria": false,
  "status": null,
  "tipo_imovel": null
}
```

### 4.2 Campos

| Campo | Tipo | Obrigatório | Validação | Descrição |
|---|---|---|---|---|
| `bbox` | `BoundingBox` | Sim | — | Retângulo geográfico da área de busca |
| `bbox.min_lon` | `float` | Sim | -180 ≤ x ≤ 180, < max_lon | Longitude oeste (mínima) |
| `bbox.min_lat` | `float` | Sim | -90 ≤ x ≤ 90, < max_lat | Latitude sul (mínima) |
| `bbox.max_lon` | `float` | Sim | -180 ≤ x ≤ 180 | Longitude leste (máxima) |
| `bbox.max_lat` | `float` | Sim | -90 ≤ x ≤ 90 | Latitude norte (máxima) |
| `uf` | `string` (enum) | Sim | Sigla de UF válida (27 estados) | Estado — determina qual camada WFS consultar |
| `max_resultados` | `int` | Não | 1 ≤ x ≤ 5000, default `50` | Número máximo de imóveis a retornar |
| `incluir_geometria` | `bool` | Não | default `false` | Se `true`, inclui o MultiPolygon de cada imóvel |
| `status` | `string` (enum) | Não | `AT`, `PE`, `CA`, `IN`, `RE`, `SU` | Filtrar por status (aplicado client-side) |
| `tipo_imovel` | `string` (enum) | Não | `IRU`, `PCT`, `AST` | Filtrar por tipo de imóvel (aplicado client-side) |

### 4.3 Enums de referência

**UF:**
`AC`, `AL`, `AM`, `AP`, `BA`, `CE`, `DF`, `ES`, `GO`, `MA`, `MG`, `MS`, `MT`, `PA`, `PB`, `PE`, `PI`, `PR`, `RJ`, `RN`, `RO`, `RR`, `RS`, `SC`, `SE`, `SP`, `TO`

**StatusImovel:**

| Código | Descrição |
|---|---|
| `AT` | Ativo |
| `PE` | Pendente |
| `CA` | Cancelado |
| `IN` | Inscrito |
| `RE` | Retificado |
| `SU` | Suspenso |

**TipoImovel:**

| Código | Descrição |
|---|---|
| `IRU` | Imóvel Rural |
| `PCT` | Povos e Comunidades Tradicionais |
| `AST` | Assentamento da Reforma Agrária |

---

## 5. Response

### 5.1 Sucesso — `200 OK`

**Modelo: `ConsultaCarBboxResponse`**

```json
{
  "total_encontrados": 424,
  "total_retornados": 2,
  "bbox_consultado": {
    "min_lon": -47.1,
    "min_lat": -23.6,
    "max_lon": -47.0,
    "max_lat": -23.5
  },
  "uf": "SP",
  "srs": "EPSG:4674",
  "filtros_aplicados": {},
  "imoveis": [
    {
      "id": "sicar_imoveis_sp.1199503",
      "cod_imovel": "SP-3550605-BA021C304C504869A0BDDA5BA55B40C0",
      "status_imovel": "AT",
      "status_descricao": "Ativo",
      "tipo_imovel": "IRU",
      "tipo_descricao": "Imóvel Rural",
      "area_hectares": 0.1025,
      "modulos_fiscais": 0.0085,
      "uf": "SP",
      "municipio": "São Roque",
      "cod_municipio_ibge": 3550605,
      "condicao": "Analisado, aguardando atendimento a notificação",
      "data_criacao": "2015-06-24T12:32:44.749Z",
      "geometria": null
    }
  ]
}
```

### 5.2 Campos do Response

| Campo | Tipo | Descrição |
|---|---|---|
| `total_encontrados` | `int` | Total de imóveis que intersectam o BBox no GeoServer (antes de filtros client-side) |
| `total_retornados` | `int` | Quantidade efetivamente retornada nesta resposta |
| `bbox_consultado` | `BoundingBox` | Echo do BBox utilizado |
| `uf` | `string` | Estado consultado |
| `srs` | `string` | Sistema de referência espacial (fixo: `EPSG:4674`) |
| `filtros_aplicados` | `object` | Filtros de atributo que foram aplicados client-side (ex.: `{"status_imovel": "AT"}`) |
| `imoveis` | `ImovelRural[]` | Lista de imóveis encontrados |

### 5.3 Campos de cada `ImovelRural`

| Campo | Tipo | Sempre presente | Descrição |
|---|---|---|---|
| `id` | `string` | Sim | ID interno do GeoServer |
| `cod_imovel` | `string` | Sim | **Código CAR** (formato: `UF-CodMunicipioIBGE-Hash`) |
| `status_imovel` | `string` | Sim | Código do status |
| `status_descricao` | `string` | Sim | Descrição legível do status |
| `tipo_imovel` | `string` | Sim | Código do tipo |
| `tipo_descricao` | `string` | Sim | Descrição legível do tipo |
| `area_hectares` | `float` | Sim | Área em hectares |
| `modulos_fiscais` | `float` | Sim | Área em módulos fiscais |
| `uf` | `string` | Sim | Sigla do estado |
| `municipio` | `string` | Sim | Nome do município |
| `cod_municipio_ibge` | `int` | Sim | Código IBGE do município |
| `condicao` | `string?` | Não | Condição da análise ambiental |
| `data_criacao` | `datetime?` | Não | Data de criação do registro |
| `geometria` | `Geometria?` | Não | MultiPolygon GeoJSON (somente se `incluir_geometria=true`) |

### 5.4 Erros

**`422 Unprocessable Entity` — Validação**

```json
{
  "erro": "VALIDACAO",
  "mensagem": "Erro de validação nos dados de entrada",
  "detalhes": [
    {
      "campo": "bbox.min_lon",
      "mensagem": "min_lon (-47.0) deve ser menor que max_lon (-47.1)"
    }
  ]
}
```

**`400 Bad Request` — UF inválida**

```json
{
  "erro": "UF_INVALIDA",
  "mensagem": "A UF 'XX' não é válida. Use uma das 27 siglas de estado.",
  "detalhes": []
}
```

**`502 Bad Gateway` — GeoServer indisponível**

```json
{
  "erro": "GEOSERVER_INDISPONIVEL",
  "mensagem": "Não foi possível conectar ao GeoServer do SICAR. Tente novamente em alguns instantes.",
  "detalhes": []
}
```

**`504 Gateway Timeout` — Timeout do GeoServer**

```json
{
  "erro": "GEOSERVER_TIMEOUT",
  "mensagem": "O GeoServer não respondeu dentro do tempo limite (60s). Tente com um BBox menor.",
  "detalhes": []
}
```

---

## 6. Lógica de Implementação

### 6.1 Fluxo

```
Request (POST /api/car/bbox)
  │
  ├─ 1. Validar request (Pydantic)
  │     • BBox: coordenadas dentro dos limites, min < max
  │     • UF: enum válido
  │     • max_resultados: 1..5000
  │
  ├─ 2. Montar URL WFS
  │     • Layer: sicar_imoveis_{uf}
  │     • BBOX: min_lon,min_lat,max_lon,max_lat,EPSG:4674
  │     • MAXFEATURES: max_resultados (ou max_resultados * 10 se há filtros)
  │     • PROPERTYNAME: campos sem geometria (se incluir_geometria=false)
  │
  ├─ 3. Chamar GeoServer WFS
  │     • SSL context com SECLEVEL=1
  │     • Timeout: 60 segundos
  │     • User-Agent customizado
  │
  ├─ 4. Tratar erros de rede
  │     • HTTPError → mapear para 502/504
  │     • URLError → mapear para 502
  │     • Timeout → mapear para 504
  │
  ├─ 5. Aplicar filtros client-side (se houver)
  │     • status: filtrar por status_imovel
  │     • tipo_imovel: filtrar por tipo_imovel
  │     • Limitar a max_resultados após filtragem
  │
  ├─ 6. Converter GeoJSON → Response
  │     • feature_to_imovel() para cada feature
  │     • Traduzir códigos para descrições legíveis
  │
  └─ 7. Retornar ConsultaCarBboxResponse
```

### 6.2 Montagem da URL WFS

```
https://geoserver.car.gov.br/geoserver/sicar/wfs?
  SERVICE=WFS&
  VERSION=1.1.0&
  REQUEST=GetFeature&
  TYPENAMES=sicar_imoveis_{uf}&
  BBOX={min_lon},{min_lat},{max_lon},{max_lat},EPSG:4674&
  OUTPUTFORMAT=application/json&
  MAXFEATURES={max_resultados}
```

Se `incluir_geometria=false`, adicionar:

```
&PROPERTYNAME=cod_imovel,status_imovel,dat_criacao,area,condicao,uf,municipio,cod_municipio_ibge,m_fiscal,tipo_imovel
```

Isso faz o GeoServer retornar `"geometry": null`, reduzindo o payload significativamente.

### 6.3 SSL

O GeoServer do SICAR requer configuração SSL relaxada:

```python
ctx = ssl.create_default_context()
ctx.set_ciphers("DEFAULT@SECLEVEL=1")
```

---

## 7. Artefatos Existentes

Os seguintes artefatos já foram criados e podem ser reutilizados:

| Artefato | Descrição |
|---|---|
| `models.py` | Models Pydantic v2 completos (Request, Response, Enums, Errors) |
| `consulta_car_bbox.py` | Função `consultar_cars_bbox()` que faz a chamada WFS |
| `models.py` → `geojson_to_response()` | Converte GeoJSON bruto → `ConsultaCarBboxResponse` |
| `models.py` → `feature_to_imovel()` | Converte feature GeoJSON → `ImovelRural` |

---

## 8. Exemplo de Integração (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from models import (
    ConsultaCarBboxRequest,
    ConsultaCarBboxResponse,
    ErrorResponse,
    geojson_to_response,
)
from consulta_car_bbox import consultar_cars_bbox

app = FastAPI()


@app.post(
    "/api/car/bbox",
    response_model=ConsultaCarBboxResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Erro de validação"},
        502: {"model": ErrorResponse, "description": "GeoServer indisponível"},
        504: {"model": ErrorResponse, "description": "Timeout do GeoServer"},
    },
)
def consultar_car_por_bbox(request: ConsultaCarBboxRequest):
    try:
        geojson = consultar_cars_bbox(
            bbox=request.bbox.to_wfs_string(),
            uf=request.uf.value.lower(),
            max_features=request.max_resultados if not request.status else request.max_resultados * 10,
            com_geometria=request.incluir_geometria,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail={
            "erro": "GEOSERVER_INDISPONIVEL",
            "mensagem": str(e),
            "detalhes": [],
        })

    return geojson_to_response(geojson, request)
```

---

## 9. Critérios de Aceite

- [ ] Endpoint `POST /api/car/bbox` registrado e acessível
- [ ] Request validado conforme modelo (BBox, UF, limites numéricos)
- [ ] Chamada ao GeoServer WFS com BBOX + MAXFEATURES + PROPERTYNAME
- [ ] Retorno correto com `cod_imovel` (código CAR) de cada imóvel no BBox
- [ ] Filtros opcionais (status, tipo_imovel) aplicados client-side
- [ ] `incluir_geometria=true` retorna MultiPolygon; `false` retorna `null`
- [ ] Erros de rede/timeout mapeados para 502/504 com `ErrorResponse`
- [ ] Erros de validação retornam 422 com detalhes dos campos inválidos
- [ ] Response inclui metadados: total_encontrados, total_retornados, bbox_consultado, filtros_aplicados
- [ ] SSL configurado com `SECLEVEL=1` para compatibilidade com o GeoServer

---

## 10. Observações Técnicas

1. **Performance:** O GeoServer pode ser lento para BBoxes muito grandes (todo um estado). Considerar limitar a área máxima do BBox ou implementar timeout com retry.

2. **Volume:** Alguns BBoxes podem conter milhares de imóveis. O campo `max_resultados` (até 5000) controla isso, mas um BBox de estado inteiro pode ter 500k+ registros.

3. **Filtros server-side bloqueados:** O WAF da Dataprev bloqueia `CQL_FILTER`. Se no futuro for liberado, a filtragem por status/tipo pode ser movida para server-side, melhorando a performance.

4. **Cache:** Como os dados do CAR não mudam com frequência, considerar cache de curta duração (5-15 min) por combinação de `uf + bbox + incluir_geometria`.

5. **PROPERTYNAME para payload leve:** Quando `incluir_geometria=false`, a exclusão da geometria no `PROPERTYNAME` reduz o tamanho do response WFS em ~80%.
