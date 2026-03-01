# Análise Técnica do Mapa — Consulta Pública CAR

**URL:** https://consultapublica.car.gov.br/publico/imoveis/index  
**Data da análise:** 28 de fevereiro de 2026

---

## 1. Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Frontend (mapa interativo) | **Leaflet.js** |
| Servidor de mapas | **GeoServer** (`geoserver.car.gov.br`) |
| Protocolo de renderização | **WMS 1.3.0** (Web Map Service) |
| Base cartográfica | ESRI World Imagery (tiles) |
| Sistema de referência | **EPSG:4674** (SIRGAS 2000) |
| Workspace GeoServer | `sicar` |

### Bibliotecas JavaScript carregadas

| Arquivo | Função |
|---|---|
| `leaflet.js` | Motor principal do mapa |
| `Leaflet.GoogleMutant.js` | Suporte a camadas Google Maps |
| `leaflet.edgebuffer.js` | Buffer de tiles nas bordas |
| `Leaflet.GraphicScale.js` | Barra de escala gráfica |
| `leaflet-search.js` | Busca por município/CAR |
| `easy-button.js` | Botões customizados (ex.: centralizar no Brasil) |
| `layers/ufs.js` | Camada de estados (UFs) |
| `layers/cidades.js` | Camada de municípios |
| `layers/cidade.js` | Handler de município individual (carrega imóveis) |
| `layers/imovel.js` | Handler de imóvel individual (popup, download) |
| `layers/wmsTile.js` | Fábrica de camadas WMS |
| `layers/camadas.js` | Gerenciamento de camadas temáticas |
| `layers/arvoreCamadas.js` | Árvore de seleção de camadas |
| `menuLayers.js` | Menu lateral de camadas |
| `imoveis.js` | Inicialização geral do mapa |

---

## 2. Camadas WMS Disponíveis (GeoServer)

O GeoServer expõe **27 camadas WMS** no workspace `sicar`, uma por estado:

| Camada | UF | Camada | UF |
|---|---|---|---|
| `sicar_imoveis_ac` | Acre | `sicar_imoveis_pb` | Paraíba |
| `sicar_imoveis_al` | Alagoas | `sicar_imoveis_pe` | Pernambuco |
| `sicar_imoveis_am` | Amazonas | `sicar_imoveis_pi` | Piauí |
| `sicar_imoveis_ap` | Amapá | `sicar_imoveis_pr` | Paraná |
| `sicar_imoveis_ba` | Bahia | `sicar_imoveis_rj` | Rio de Janeiro |
| `sicar_imoveis_ce` | Ceará | `sicar_imoveis_rn` | Rio Grande do Norte |
| `sicar_imoveis_df` | Distrito Federal | `sicar_imoveis_ro` | Rondônia |
| `sicar_imoveis_es` | Espírito Santo | `sicar_imoveis_rr` | Roraima |
| `sicar_imoveis_go` | Goiás | `sicar_imoveis_rs` | Rio Grande do Sul |
| `sicar_imoveis_ma` | Maranhão | `sicar_imoveis_sc` | Santa Catarina |
| `sicar_imoveis_mg` | Minas Gerais | `sicar_imoveis_se` | Sergipe |
| `sicar_imoveis_ms` | Mato Grosso do Sul | `sicar_imoveis_sp` | São Paulo |
| `sicar_imoveis_mt` | Mato Grosso | `sicar_imoveis_to` | Tocantins |
| `sicar_imoveis_pa` | Pará | | |

### Características das camadas

- **Tipo de geometria:** MultiPolygon
- **queryable:** `1` (suporta GetFeatureInfo)
- **SRS:** EPSG:4674
- **Estilo padrão:** `polygon` ("Default Polygon")

### Exemplo de BoundingBox (SP)

```
LatLonBoundingBox: minx="-53.10" miny="-25.25" maxx="-44.17" maxy="-19.30"
```

---

## 3. Como o Mapa é Renderizado (Pintado)

### 3.1 Tiles WMS (visão geral dos perímetros)

O mapa **não** envia polígonos vetoriais individuais ao navegador para a visualização geral. O processo é:

1. O Leaflet calcula o **BBOX** (Bounding Box) da área visível na tela
2. Para cada tile visível, envia uma requisição **WMS GetMap** ao GeoServer
3. O GeoServer:
   - Filtra os polígonos que intersectam o BBOX solicitado
   - Aplica o filtro CQL: `ind_status_imovel IN ('AT','SU','PE')`
   - **Renderiza uma imagem PNG server-side** com os polígonos desenhados
   - Retorna a imagem ao navegador
4. O Leaflet sobrepõe as imagens PNG sobre o mapa base

#### Código fonte (`wmsTile.js`)

```javascript
function WMSTile(layer, open, layerNameDescribeGroup) {
    var geoserver = '../mosaicos/getGeoserverImages';

    var tile = L.tileLayer.wms(geoserver, {
        layers: isNaN(layer) ? layer : 'secar-pa:rel_tema_imovel_poligono',
        format: 'image/png',
        transparent: true,
        version: '1.3.0',
        tiled: true
    });

    // ...

    return isNaN(layer) ? tile : tile.setParams({
        'CQL_FILTER': 'idt_tema=' + layer
    });
}
```

#### Exemplo de URL WMS GetMap

```
https://geoserver.car.gov.br/geoserver/sicar/wms?
  SERVICE=WMS&
  VERSION=1.3.0&
  REQUEST=GetMap&
  LAYERS=sicar_imoveis_sp&
  BBOX=-47.1,-23.6,-47.0,-23.5&
  WIDTH=256&
  HEIGHT=256&
  SRS=EPSG:4674&
  FORMAT=image/png&
  TRANSPARENT=true
```

> **O BBOX define a janela geográfica a renderizar, NÃO a geometria do imóvel.** As geometrias reais são MultiPolygons armazenados no GeoServer.

### 3.2 Imóvel individual (renderização vetorial)

Quando um imóvel específico é selecionado, ele é renderizado como **camada vetorial Leaflet** (não mais como imagem WMS), com estilo destacado:

```javascript
imovel.setStyle({
    color: '#ffff00',      // borda amarela
    dashArray: '1, 5',     // tracejado
    fillColor: 'transparent',
    weight: 5
});
```

---

## 4. Fluxo de Navegação e Identificação do CAR

### 4.1 Hierarquia de navegação

```
Brasil → Estado (UF) → Município → Imóvel Rural (CAR)
```

### 4.2 Fluxo detalhado

```
┌──────────────┐                          ┌──────────────┐
│  imoveis.js  │  Inicializa mapa         │  GeoServer   │
│  (Leaflet)   │  com bounds do Brasil    │  (WMS)       │
└──────┬───────┘                          └──────────────┘
       │
       │ Click no estado
       ▼
┌──────────────┐  GET ../estados/getEstadoFeature
│   ufs.js     │ ────────────────────────────────> Backend
│              │ <──────────────── GeoJSON do estado
└──────┬───────┘
       │
       │ Zoom no estado → carrega municípios
       ▼
┌──────────────┐  GET ../municipios/getMunicipiosFeature?estado[id]=XX
│  cidades.js  │ ────────────────────────────────> Backend
│              │ <──────────────── GeoJSON dos municípios
└──────┬───────┘
       │
       │ Click no município
       ▼
┌──────────────┐  GET getImovel?lat=Y&lng=X
│  cidade.js   │ ────────────────────────────────> Backend
│              │ <──────────────── GeoJSON do imóvel
└──────┬───────┘
       │
       │ Cria camada vetorial do imóvel
       ▼
┌──────────────┐
│  imovel.js   │  Renderiza polígono + popup com dados
└──────────────┘
```

### 4.3 Identificação do imóvel ao clicar

Quando o usuário clica dentro de um município, o sistema **não usa BBOX** para identificar o imóvel. O processo é:

1. Leaflet captura as coordenadas `lat` e `lng` do ponto clicado
2. Envia uma requisição ao endpoint `getImovel`:

```javascript
// cidade.js
cidade.on('click', function(e) {
    $.getJSON('getImovel', {
        lat: e.latlng.lat,
        lng: e.latlng.lng
    }).done(function(listaImovel) {
        L.geoJSON(listaImovel, {
            onEachFeature: function (feature, l) {
                new Imovel(l, imoveis, map);
            }
        });
    });
});
```

3. O backend executa uma **consulta espacial point-in-polygon** (ST_Contains / ST_Intersects) no banco de dados
4. Retorna o GeoJSON do imóvel que contém aquele ponto

---

## 5. Estrutura dos Dados Retornados (GeoJSON)

### 5.1 Atributos do imóvel (via WMS GetFeatureInfo)

Testado com:
```
GET https://geoserver.car.gov.br/geoserver/sicar/wms?
  SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&
  LAYERS=sicar_imoveis_sp&QUERY_LAYERS=sicar_imoveis_sp&
  INFO_FORMAT=application/json&SRS=EPSG:4674&
  BBOX=-47.1,-23.6,-47.0,-23.5&WIDTH=256&HEIGHT=256&
  X=128&Y=128&FEATURE_COUNT=1
```

Resposta:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "sicar_imoveis_sp.14698657",
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[
          [-47.049, -23.552],
          [-47.0461, -23.5502],
          [-47.048, -23.5463],
          [-47.0478, -23.5425],
          [-47.0495, -23.5433],
          [-47.0489, -23.5463],
          [-47.0501, -23.5465],
          [-47.049, -23.552]
        ]]]
      },
      "geometry_name": "geo_area_imovel",
      "properties": {
        "cod_imovel": "SP-3550605-CBBE65147FFD4CC2ACB401BECE5033E5",
        "status_imovel": "AT",
        "dat_criacao": "2025-09-10T06:26:39.735Z",
        "area": 21.7038,
        "condicao": "Analisado, em conformidade com a Lei nº 12.651/2012",
        "uf": "SP",
        "municipio": "São Roque",
        "cod_municipio_ibge": 3550605,
        "m_fiscal": 1.8092,
        "tipo_imovel": "IRU"
      }
    }
  ],
  "crs": {
    "type": "name",
    "properties": {
      "name": "urn:ogc:def:crs:EPSG::4674"
    }
  }
}
```

### 5.2 Descrição dos campos

| Campo | Descrição | Exemplo |
|---|---|---|
| `cod_imovel` | Código CAR completo (UF-CodMunIBGE-Hash) | `SP-3550605-CBBE65147FFD4CC2ACB401BECE5033E5` |
| `status_imovel` | Status do cadastro | `AT` (Ativo), `PE` (Pendente), `CA` (Cancelado), `IN` (Inscrito), `RE` (Retificado) |
| `dat_criacao` | Data de criação do registro | `2025-09-10T06:26:39.735Z` |
| `area` | Área em hectares | `21.7038` |
| `condicao` | Condição de análise | `Analisado, em conformidade com a Lei nº 12.651/2012` |
| `uf` | Sigla do estado | `SP` |
| `municipio` | Nome do município | `São Roque` |
| `cod_municipio_ibge` | Código IBGE do município | `3550605` |
| `m_fiscal` | Módulos fiscais | `1.8092` |
| `tipo_imovel` | Tipo de imóvel | `IRU` (Rural), `PCT` (Povos/Comunidades Tradicionais), `AST` (Assentamentos) |
| `geometry_name` | Nome da coluna geométrica | `geo_area_imovel` |

### 5.3 Popup do imóvel (frontend)

O popup exibido na interface mostra:
- Código CAR
- Status do cadastro
- Tipo de imóvel
- Município
- Área (ha)
- Data de atualização
- Botão **"Demonstrativo"** → abre a página de consulta individual
- Botão **"Download Shapefile"** → exporta geometria (com captcha)

---

## 6. Endpoints Identificados

| Endpoint | Método | Descrição |
|---|---|---|
| `../mosaicos/getGeoserverImages` | WMS GetMap | Proxy para tiles WMS do GeoServer |
| `getImovel?lat=Y&lng=X` | GET | Retorna GeoJSON do imóvel na coordenada |
| `../municipios/getMunicipiosFeature?estado[id]=XX` | GET | GeoJSON dos municípios de um estado |
| `../estados/getEstadoFeature` | GET | GeoJSON dos estados |
| `quantitativoImoveis` | GET | Estatísticas (total, área, percentuais) |
| `exportShapeFile?idImovel=ID&ReCaptcha=CODE` | GET | Download do shapefile |
| `../municipios/ReCaptcha?id=RAND` | GET | Imagem captcha para download |

### WMS GeoServer (direto)

| URL base | Operações |
|---|---|
| `https://geoserver.car.gov.br/geoserver/sicar/wms` | GetMap, GetFeatureInfo, GetCapabilities, DescribeLayer, GetLegendGraphic |

### Formatos suportados pelo GetFeatureInfo

- `text/plain`
- `application/vnd.ogc.gml`
- `text/xml`
- `application/vnd.ogc.gml/3.1.1`
- `text/html`
- `application/json`

---

## 7. Respostas às Perguntas

### O BBOX é utilizado para montar cada área rural no mapa?

**Não.** O BBOX é um parâmetro do protocolo WMS que define a janela geográfica (retângulo de coordenadas) que o servidor deve renderizar como imagem. As áreas rurais são geometrias MultiPolygon armazenadas no banco de dados do GeoServer. O BBOX apenas informa "renderize todos os polígonos que estiverem dentro deste retângulo".

### Como é "pintado" o mapa?

Por **WMS tiles server-side rendering**:
1. O GeoServer recebe o BBOX + dimensões do tile
2. Filtra polígonos que intersectam o BBOX
3. Desenha os polígonos numa imagem PNG no servidor
4. Envia a imagem pronta ao navegador
5. O Leaflet sobrepõe as imagens sobre o mapa base (satélite ESRI)

### Como o sistema sabe que quero um CAR específico ao clicar?

Pelo **ponto (lat/lng) do clique**, não pelo BBOX. O backend recebe as coordenadas do clique e executa uma consulta espacial (point-in-polygon) no banco para encontrar qual imóvel contém aquele ponto. Retorna o GeoJSON completo (geometria + atributos) do imóvel encontrado.

---

## 8. Consulta de CARs por BBOX via WFS

### O GeoServer também expõe WFS (Web Feature Service)

Além do WMS (que retorna imagens), o GeoServer do SICAR possui um endpoint **WFS público** que retorna **dados vetoriais (GeoJSON)** dos imóveis dentro de um BBOX.

### Endpoint WFS

```
https://geoserver.car.gov.br/geoserver/sicar/wfs
```

### Exemplo de requisição — listar CARs dentro de um BBOX

```
GET https://geoserver.car.gov.br/geoserver/sicar/wfs?
  SERVICE=WFS&
  VERSION=1.1.0&
  REQUEST=GetFeature&
  TYPENAMES=sicar_imoveis_sp&
  BBOX=-47.1,-23.6,-47.0,-23.5,EPSG:4674&
  OUTPUTFORMAT=application/json&
  MAXFEATURES=50
```

### Parâmetros

| Parâmetro | Descrição | Exemplo |
|---|---|---|
| `SERVICE` | Tipo de serviço | `WFS` |
| `VERSION` | Versão do protocolo | `1.1.0` |
| `REQUEST` | Operação | `GetFeature` |
| `TYPENAMES` | Camada (layer) = `sicar_imoveis_{uf}` | `sicar_imoveis_sp` |
| `BBOX` | Bounding Box: `minLon,minLat,maxLon,maxLat,SRS` | `-47.1,-23.6,-47.0,-23.5,EPSG:4674` |
| `OUTPUTFORMAT` | Formato de saída | `application/json` |
| `MAXFEATURES` | Limite de resultados | `50` |
| `PROPERTYNAME` | Campos específicos (opcional, omitir para incluir geometria) | `cod_imovel,area,municipio` |

### Exemplo de resposta (testado com sucesso)

```json
{
  "type": "FeatureCollection",
  "totalFeatures": 424,
  "numberReturned": 3,
  "features": [
    {
      "type": "Feature",
      "id": "sicar_imoveis_sp.1199503",
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[-47.0778,-23.5424], [-47.0775,-23.5423], ...]]]
      },
      "properties": {
        "cod_imovel": "SP-3550605-BA021C304C504869A0BDDA5BA55B40C0",
        "status_imovel": "AT",
        "area": 0.1025,
        "municipio": "São Roque",
        "tipo_imovel": "IRU"
      }
    }
  ]
}
```

> **424 imóveis foram encontrados** no BBOX `-47.1,-23.6,-47.0,-23.5` (região de São Roque/SP).

### Sem geometria (resposta leve)

Adicionando `PROPERTYNAME` para excluir a geometria:

```
&PROPERTYNAME=cod_imovel,status_imovel,dat_criacao,area,condicao,uf,municipio,cod_municipio_ibge,m_fiscal,tipo_imovel
```

Retorna `"geometry": null`, reduzindo significativamente o tamanho da resposta.

### Limitações identificadas

- **CQL_FILTER bloqueado:** o WAF (Dataprev) em frente ao GeoServer bloqueia requisições que combinam `CQL_FILTER` com qualquer outro filtro. A filtragem por atributos (ex.: status) deve ser feita **client-side**.
- **BBOX e CQL_FILTER são mutuamente exclusivos** no WFS deste GeoServer.
- **MAXFEATURES padrão** pode limitar resultados. Para grandes áreas, aumente o valor ou pagine com `STARTINDEX`.

### Script Python utilitário

O script `consulta_car_bbox.py` neste repositório implementa a consulta completa:

```bash
# Listar CARs no BBOX
python consulta_car_bbox.py --bbox="-47.1,-23.6,-47.0,-23.5" --uf sp --max 50

# Filtrar por status (Ativo)
python consulta_car_bbox.py --bbox="-47.1,-23.6,-47.0,-23.5" --uf sp --status AT

# Com geometria + salvar em arquivo
python consulta_car_bbox.py --bbox="-47.1,-23.6,-47.0,-23.5" --uf sp --com-geometria --output resultado.json

# Saída em JSON
python consulta_car_bbox.py --bbox="-47.1,-23.6,-47.0,-23.5" --uf sp --json
```
