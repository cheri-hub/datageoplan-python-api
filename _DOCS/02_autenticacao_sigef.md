# Autenticação Gov.br no SIGEF INCRA

## Objetivo
Usar a sessão autenticada do Gov.br para acessar o SIGEF (Sistema de Gestão Fundiária) do INCRA.

---

## Fluxo de Autenticação

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Gov.br    │───▶│   OAuth     │───▶│    SIGEF    │
│   Login     │    │  Redirect   │    │   Logado    │
└─────────────┘    └─────────────┘    └─────────────┘
```

1. Usuário faz login no Gov.br com certificado digital
2. Gov.br redireciona para o SIGEF com token OAuth
3. SIGEF cria sessão própria (cookie `sessionid`)

---

## Solução

Carregar a sessão do Gov.br (`auth_state.json`) e navegar até o SIGEF. O Gov.br faz o redirect OAuth automaticamente.

---

## Código da Solução

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    
    # Carrega sessão do Gov.br
    context = browser.new_context(
        storage_state="auth_state.json"
    )
    
    page = context.new_page()
    
    # Acessa o SIGEF
    page.goto("https://sigef.incra.gov.br/")
    page.wait_for_load_state("networkidle")
    
    # Clica em "Entrar com Gov.br" se necessário
    # O redirect OAuth acontece automaticamente
    
    # Salva sessão combinada (Gov.br + SIGEF)
    context.storage_state(path="auth_state_sigef.json")
```

---

## Cookies Importantes

### Gov.br
| Cookie | Descrição |
|--------|-----------|
| `Session_Gov_Br_Prod` | Sessão do Gov.br |
| `Govbrid` | ID único do usuário |

### SIGEF
| Cookie | Descrição | Validade |
|--------|-----------|----------|
| `sessionid` | Sessão do SIGEF | ~4 horas |
| `TS0128ff67` | Token de segurança | Sessão |

---

## Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `auth_state.json` | Sessão Gov.br |
| `auth_state_sigef.json` | Sessão Gov.br + SIGEF |
| `cookies_sigef.json` | Cookies do SIGEF |

---

## Scripts Criados

| Script | Função |
|--------|--------|
| `acessar_sigef.py` | Acessa SIGEF usando sessão Gov.br |
| `sigef_autenticado.py` | Reutiliza sessão SIGEF existente |

---

## Uso

```bash
# Primeiro: fazer login no Gov.br
python gravar_chrome_sistema.py

# Depois: acessar SIGEF com a sessão
python acessar_sigef.py

# Reutilizar sessão SIGEF
python sigef_autenticado.py
```

---

## Verificação de Sessão

Para verificar se a sessão está válida:

```python
import json

with open("auth_state_sigef.json", "r") as f:
    data = json.load(f)

for cookie in data["cookies"]:
    if cookie["name"] == "sessionid":
        print(f"Session ID: {cookie['value']}")
        print(f"Expira: {cookie['expires']}")
```

---

## Troubleshooting

### Problema: Sessão expirada
**Solução:** Execute `gravar_chrome_sistema.py` novamente

### Problema: SIGEF pede login novamente
**Solução:** A sessão do Gov.br pode ter expirado. Refaça o login completo.

### Problema: Certificado não aparece
**Solução:** Verifique se o certificado está instalado em:
- Windows: `certmgr.msc` → Pessoal → Certificados
