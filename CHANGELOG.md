# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.1.0] - 2024-12-28

### Adicionado
- **Download de Memorial Descritivo (PDF)**: Nova funcionalidade para baixar o memorial descritivo oficial das parcelas SIGEF
  - Endpoint REST: `GET /api/v1/sigef/memorial/{codigo}`
  - Método no cliente SIGEF: `download_memorial()`
  - Método no serviço: `download_memorial()`
  - Suporte a retry automático com backoff exponencial
  - Validação de Content-Type (PDF vs HTML)
  - Re-autenticação automática em caso de sessão expirada
  - Interface no frontend com botão "Baixar Memorial (PDF)"
  - Documentação completa em `_DOCS/04_memorial_descritivo.md`

### Modificado
- **README.md**: Atualizado com referência ao memorial descritivo
- **_DOCS/03_download_csv_sigef.md**: Adicionada API do memorial na tabela de endpoints
- Interface `ISigefClient`: Adicionado método abstrato `download_memorial()`
- Frontend: Novo ícone `FileText` para memorial descritivo

### Corrigido
- N/A

---

## [1.0.0] - 2024-12-XX

### Adicionado
- **Autenticação Gov.br**: Login via certificado digital A1
  - Suporte a Chrome do sistema (channel="chrome")
  - Captura completa de sessão (cookies + localStorage)
  - Persistência de sessão em JSON
  - Validação e refresh automático de sessão

- **Integração SIGEF INCRA**: 
  - Autenticação OAuth via Gov.br
  - Gestão automática de cookies
  - Re-autenticação transparente

- **Download de CSVs**:
  - Parcela, Vértice e Limites
  - Download individual ou em lote
  - Retry automático com backoff exponencial
  - Validação de código de parcela (UUID)

- **API REST com FastAPI**:
  - Documentação automática (Swagger/OpenAPI)
  - Validação de requests com Pydantic
  - Tratamento de erros customizado
  - CORS configurável
  - Logging estruturado com structlog

- **Arquitetura Enterprise**:
  - Clean Architecture (Domain, Application, Infrastructure, Presentation)
  - Princípios SOLID aplicados
  - Dependency Injection
  - Repository Pattern
  - Interface Segregation

- **Frontend React**:
  - Interface moderna com Tailwind CSS
  - Componentes reutilizáveis
  - TypeScript para type safety
  - Integração com API REST
  - Download direto no navegador

- **Testes Automatizados**:
  - 18 testes unitários
  - Cobertura de domínio e API
  - Mocks para serviços externos
  - Execução rápida (~0.2s)

- **Documentação Técnica**:
  - `_DOCS/01_login_govbr.md`: Processo de autenticação
  - `_DOCS/02_autenticacao_sigef.md`: Fluxo OAuth
  - `_DOCS/03_download_csv_sigef.md`: APIs de download

- **Infraestrutura**:
  - Dockerfile para containerização
  - docker-compose.yml para orquestração
  - Configuração via variáveis de ambiente
  - Suporte a múltiplos ambientes (dev/staging/prod)

### Características Técnicas
- Python 3.11+
- FastAPI 0.104+
- Playwright 1.40+
- React 18
- TypeScript 5
- Tailwind CSS 3

---

## Tipos de Mudanças
- `Adicionado` para novas funcionalidades
- `Modificado` para mudanças em funcionalidades existentes
- `Obsoleto` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correções de bugs
- `Segurança` para vulnerabilidades

---

[1.1.0]: https://github.com/example/gov-auth/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/example/gov-auth/releases/tag/v1.0.0
