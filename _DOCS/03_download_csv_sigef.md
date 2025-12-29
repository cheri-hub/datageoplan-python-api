# Download CSV do SIGEF via API

## Objetivo
Baixar dados de parcelas (Parcela, Vértices e Limites) diretamente via API HTTP, sem precisar abrir navegador.

---

## APIs Mapeadas

| Tipo | URL | Método |
|------|-----|--------|
| Parcela | `https://sigef.incra.gov.br/geo/exportar/parcela/csv/{codigo}/` | GET |
| Vértices | `https://sigef.incra.gov.br/geo/exportar/vertice/csv/{codigo}/` | GET |
| Limites | `https://sigef.incra.gov.br/geo/exportar/limite/csv/{codigo}/` | GET |
| Memorial | `https://sigef.incra.gov.br/geo/parcela/memorial/{codigo}/` | GET |

---

## Como Descobrimos as APIs

1. Criamos um script para interceptar requisições HTTP do navegador
2. Acessamos a página da parcela no SIGEF
3. Clicamos nos botões de download CSV
4. Capturamos as URLs chamadas

### Script de Mapeamento
```python
# sigef_mapear_apis.py
page.on("request", lambda req: print(f"{req.method} {req.url}"))
page.on("response", lambda res: print(f"[{res.status}] {res.url}"))
```

### Resultado do Mapeamento
```
🔗 GET https://sigef.incra.gov.br/geo/exportar/parcela/csv/999a354b-.../
📥 [200] Content-Type: text/csv

🔗 GET https://sigef.incra.gov.br/geo/exportar/vertice/csv/999a354b-.../
📥 [200] Content-Type: text/csv

🔗 GET https://sigef.incra.gov.br/geo/exportar/limite/csv/999a354b-.../
📥 [200] Content-Type: text/csv
```

---

## Código da Solução

```python
import requests
import json

# Carrega cookies da sessão
with open("auth_state_sigef.json", "r") as f:
    data = json.load(f)

# Extrai cookies do SIGEF
cookies = {}
for cookie in data["cookies"]:
    if "sigef" in cookie["domain"] or "incra" in cookie["domain"]:
        cookies[cookie["name"]] = cookie["value"]

# Headers necessários
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "referer": "https://sigef.incra.gov.br/geo/parcela/detalhe/{codigo}/",
}

# Cria sessão
session = requests.Session()
for name, value in cookies.items():
    session.cookies.set(name, value, domain="sigef.incra.gov.br")

# Baixa CSV
codigo = "999a354b-0c33-46a2-bfb3-28213892d541"
url = f"https://sigef.incra.gov.br/geo/exportar/parcela/csv/{codigo}/"

response = session.get(url, headers=headers)

if response.status_code == 200:
    with open("parcela.csv", "w") as f:
        f.write(response.text)
```

---

## Estrutura dos CSVs

### Parcela
```csv
QRCODE;NOME;GEOMETRIA_WKT;...
```
- Dados gerais da parcela
- Geometria em formato WKT

### Vértices
```csv
QRCODE;CODIGO;METODO_POSICIONAMENTO;TIPO_VERTICE;SIGMA_X;SIGMA_Y;SIGMA_Z;LADO;...
```
- Coordenadas de cada vértice
- Precisão (sigma X/Y/Z)
- Método de posicionamento (GPS, etc.)

### Limites
```csv
QRCODE;DO_VERTICE;AO_VERTICE;TIPO;AZIMUTE;COMPRIMENTO;CONFRONTANTE_DESC;...
```
- Conexões entre vértices
- Azimute e comprimento
- Descrição do confrontante

---

## Scripts Criados

| Script | Função |
|--------|--------|
| `sigef_mapear_apis.py` | Intercepta e mapeia chamadas de API |
| `sigef_api_direta.py` | Download direto via HTTP (sem navegador) |
| `sigef_download.py` | Download via navegador com Playwright |

---

## Uso

```bash
# Download via API (recomendado - mais rápido)
python sigef_api_direta.py

# Opção 1: Baixar CSVs de uma parcela
# Opção 2: Testar se a sessão é válida
```

---

## Exemplo de Saída

```
📥 Baixando parcela...
   URL: https://sigef.incra.gov.br/geo/exportar/parcela/csv/999a354b-.../
   Status: 200
   Content-Type: text/csv
   ✅ Salvo: 999a354b_parcela.csv

📥 Baixando vertice...
   ✅ Salvo: 999a354b_vertice.csv

📥 Baixando limite...
   ✅ Salvo: 999a354b_limite.csv

📄 Baixando memorial...
   URL: https://sigef.incra.gov.br/geo/parcela/memorial/999a354b-.../
   Status: 200
   Content-Type: application/pdf
   ✅ Salvo: 999a354b_memorial.pdf

✅ 4/4 arquivos baixados com sucesso
```

---

## Arquivos de Log

Os logs das APIs ficam em `logs_api/`:

| Arquivo | Conteúdo |
|---------|----------|
| `todas_requisicoes_*.json` | Todas as requisições HTTP |
| `apis_download_*.json` | Apenas requisições de download |
| `resumo_apis_*.json` | Endpoints únicos encontrados |

---

## Requisitos

```bash
pip install requests playwright
```

---

## Validade da Sessão

- **Cookie `sessionid`**: ~4 horas
- Para renovar: execute `acessar_sigef.py` novamente

---

## Outras APIs Descobertas

| URL | Descrição |
|-----|-----------|
| `/geo/parcela/detalhe/{codigo}/` | Página de detalhes || `/geo/parcela/memorial/{codigo}/` | Memorial descritivo (PDF) || `/geo/parcela/kml/{codigo}/` | Download KML |
| `/geo/parcela/plantaA4/{codigo}/` | Planta em PDF |
