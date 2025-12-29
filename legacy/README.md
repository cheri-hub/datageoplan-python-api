# Scripts Legados

Scripts de desenvolvimento e exploração usados durante a fase inicial do projeto.
Foram substituídos pela arquitetura enterprise em `src/`.

## Arquivos

| Script | Descrição |
|--------|-----------|
| `gravar_chrome_sistema.py` | Login Gov.br via Playwright + Chrome do sistema |
| `acessar_sigef.py` | Acesso ao SIGEF usando sessão Gov.br |
| `sigef_api_direta.py` | Download de CSVs via requisições HTTP diretas |
| `sigef_mapear_apis.py` | Interceptação de requests para descobrir endpoints |

## Uso

Estes scripts podem ser executados diretamente para testes rápidos:

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Login no Gov.br (interativo)
python legacy/gravar_chrome_sistema.py

# Download de CSVs
python legacy/sigef_api_direta.py
```

## Nota

Para produção, use a API enterprise em `src/`:

```bash
python -m src.main
```
