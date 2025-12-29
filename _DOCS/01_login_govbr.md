# Login no Gov.br com Certificado Digital

## Objetivo
Autenticar no portal Gov.br usando certificado digital A1 de forma automatizada, capturando a sessão para uso posterior.

---

## Problema Inicial

O Playwright usa um navegador Chromium isolado que é detectado pelos sistemas anti-bot do Gov.br, resultando em:
- CAPTCHA solicitado
- Erro `ERR_SSL_CLIENT_AUTH_CERT_NEEDED` (certificado não encontrado)

---

## Solução

Usar o **Chrome do sistema** (não o Chromium do Playwright) com a flag `channel="chrome"`. Isso permite:
- ✅ Acesso aos certificados A1 instalados no Windows
- ✅ Evita detecção de bot (menos CAPTCHA)
- ✅ Usa o perfil real do usuário

---

## Código da Solução

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",  # Usa Chrome do sistema
        headless=False,    # Precisa ser visível para selecionar certificado
        args=[
            "--disable-blink-features=AutomationControlled",  # Evita detecção
        ]
    )
    
    context = browser.new_context(
        ignore_https_errors=True
    )
    
    page = context.new_page()
    page.goto("https://sso.acesso.gov.br")
    
    # Usuário faz login manualmente com certificado
    input("Pressione ENTER após fazer login...")
    
    # Salva a sessão (cookies + localStorage)
    context.storage_state(path="auth_state.json")
```

---

## Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `auth_state.json` | Sessão completa (cookies + localStorage) |
| `cookies.json` | Apenas os cookies |

---

## Dados Capturados

O `auth_state.json` contém um JWT no localStorage com:
- **CPF** do usuário
- **Nome** completo
- **Selo da conta** (Bronze, Prata, Ouro)
- **access_token** para APIs
- **Lista de CNPJs** vinculados

---

## Scripts Criados

| Script | Função |
|--------|--------|
| `gravar_chrome_sistema.py` | Abre Chrome, faz login, salva sessão |
| `usar_sessao.py` | Reutiliza sessão salva sem novo login |

---

## Requisitos

- Python 3.10+
- Playwright (`pip install playwright`)
- Chrome instalado no sistema
- Certificado A1 instalado no Windows

---

## Instalação

```bash
pip install playwright
playwright install chromium
```

---

## Uso

```bash
# Fazer login e salvar sessão
python gravar_chrome_sistema.py

# Reutilizar sessão existente
python usar_sessao.py
```

---

## Observações

1. O certificado A1 deve estar instalado no Windows Certificate Store
2. A sessão expira após algumas horas
3. Para certificado A3 (token), pode ser necessário driver específico
