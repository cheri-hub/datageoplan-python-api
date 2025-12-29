# Download do Memorial Descritivo (PDF)

## Objetivo
Baixar o memorial descritivo de parcelas SIGEF em formato PDF via API REST.

---

## API Mapeada

| Tipo | URL | Método | Content-Type |
|------|-----|--------|-------------|
| Memorial | `https://sigef.incra.gov.br/geo/parcela/memorial/{codigo}/` | GET | application/pdf |

---

## O que é o Memorial Descritivo?

O memorial descritivo é um documento técnico que contém:
- **Descrição técnica completa** da parcela
- **Coordenadas geográficas** dos vértices
- **Azimutes e distâncias** entre pontos
- **Confrontações** (limites com propriedades vizinhas)
- **Área total** da parcela
- **Perímetro** da parcela
- **Informações do responsável técnico** (RT)

Este documento é **oficial** e pode ser usado para:
- Processos de regularização fundiária
- Documentação de propriedades rurais
- Processos judiciais
- Registro em cartório

---

## Descoberta da API

A URL do memorial foi identificada ao analisar o fluxo de navegação na página de detalhes da parcela no SIGEF:

```
Página da Parcela → Botão "Memorial Descritivo" → GET /geo/parcela/memorial/{codigo}/
```

### Requisição cURL Original

```bash
curl "https://sigef.incra.gov.br/geo/parcela/memorial/999a354b-0c33-46a2-bfb3-28213892d541/" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*" \
  -H "Accept-Language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7" \
  -H "Referer: https://sigef.incra.gov.br/geo/parcela/detalhe/999a354b-0c33-46a2-bfb3-28213892d541/" \
  -b "sessionid=xxx; csrftoken=xxx; ..." \
  --output memorial.pdf
```

---

## Implementação

### Backend (Python/FastAPI)

#### 1. Cliente SIGEF
```python
# src/infrastructure/sigef/client.py

async def download_memorial(
    self,
    codigo: str,
    session: Session,
    destino: Path | None = None,
) -> Path:
    """Baixa memorial descritivo (PDF) de uma parcela."""
    codigo = self._validate_parcela_code(codigo)
    
    url = f"{self.base_url}/geo/parcela/memorial/{codigo}/"
    
    cookies = self._build_cookies_dict(session)
    headers = self._get_headers()
    headers["Referer"] = f"{self.base_url}/geo/parcela/detalhe/{codigo}/"
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*"
    
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=60.0,
        cookies=cookies,
        headers=headers,
    ) as client:
        response = await client.get(url)
        
        if response.status_code != 200:
            raise SigefError(f"Erro ao baixar memorial: HTTP {response.status_code}")
        
        # Verifica se é PDF
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type and "application/pdf" not in content_type:
            raise SessionExpiredError("Sessão inválida. Recebido HTML ao invés de PDF.")
        
        # Salva arquivo
        if destino is None:
            destino = self.settings.downloads_dir / f"{codigo}_memorial.pdf"
        
        destino.write_bytes(response.content)
        
        return destino
```

#### 2. Serviço
```python
# src/services/sigef_service.py

async def download_memorial(
    self,
    codigo: str,
    destino: Path | str | None = None,
) -> Path:
    """Baixa memorial descritivo (PDF)."""
    destino_path = Path(destino) if destino else None
    
    async def _download(session):
        return await self.sigef.download_memorial(
            codigo=codigo,
            session=session,
            destino=destino_path,
        )
    
    return await self._execute_with_reauth(_download)
```

#### 3. Endpoint API
```python
# src/api/v1/routes/sigef.py

@router.get(
    "/memorial/{codigo}",
    summary="Download do memorial descritivo (PDF)",
    description="Retorna o memorial descritivo da parcela em formato PDF.",
    response_class=FileResponse,
)
async def download_memorial(
    codigo: str,
    sigef_service: SigefService = Depends(get_sigef_service),
):
    """Retorna memorial descritivo (PDF) para download direto."""
    path = await sigef_service.download_memorial(codigo=codigo)
    
    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/pdf",
    )
```

---

### Frontend (React/TypeScript)

#### 1. Serviço
```typescript
// frontend/src/services/sigefService.ts

export const sigefService = {
  /**
   * Download do memorial descritivo (PDF)
   */
  async downloadMemorial(codigo: string): Promise<Blob> {
    const response = await api.get(`/sigef/memorial/${codigo}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Faz download e salva memorial localmente no navegador
   */
  async downloadAndSaveMemorial(codigo: string): Promise<void> {
    const blob = await this.downloadMemorial(codigo);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${codigo}_memorial.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
```

#### 2. Componente
```tsx
// frontend/src/components/ParcelaDownload.tsx

const handleDownloadMemorial = async () => {
  if (!codigo.trim()) return;
  
  try {
    await sigefService.downloadAndSaveMemorial(codigo.trim());
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Erro ao baixar memorial');
  }
};

// UI
<div className="mt-6 pt-6 border-t">
  <h4 className="font-medium mb-3">Memorial Descritivo</h4>
  <button
    onClick={handleDownloadMemorial}
    className="btn-primary flex items-center gap-2"
  >
    <FileText className="w-4 h-4" />
    Baixar Memorial (PDF)
  </button>
</div>
```

---

## Headers Importantes

| Header | Valor | Propósito |
|--------|-------|-----------|
| `Referer` | `https://sigef.incra.gov.br/geo/parcela/detalhe/{codigo}/` | Validação de origem |
| `Accept` | `application/pdf,*/*` | Indica que aceita PDF |
| `Cookie` | `sessionid=xxx; ...` | Autenticação no SIGEF |

---

## Tratamento de Erros

| Cenário | Status | Ação |
|---------|--------|------|
| Parcela não encontrada | 404 | Lança `ParcelaNotFoundError` |
| Sessão expirada | 401 ou HTML | Lança `SessionExpiredError` |
| Erro no servidor | 500 | Lança `SigefError` |
| Código inválido | 400 | Lança `InvalidParcelaCodeError` |

---

## Validação de Resposta

### Content-Type
O backend valida o `Content-Type` da resposta:

```python
content_type = response.headers.get("content-type", "")
if "text/html" in content_type and "application/pdf" not in content_type:
    raise SessionExpiredError("Sessão inválida. Recebido HTML ao invés de PDF.")
```

**Por quê?**
- Se a sessão expirou, o SIGEF redireciona para a página de login
- A resposta será HTML (página de login) ao invés de PDF
- Isso indica que é necessário re-autenticar

---

## Retry Automático

O download do memorial usa retry com backoff exponencial:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def download_memorial(...):
    ...
```

**Tentativas:**
1. Tentativa imediata
2. Aguarda 2 segundos → tenta novamente
3. Aguarda 4 segundos → tenta novamente
4. Aguarda 8 segundos → tenta novamente

Se todas falharem, lança exceção.

---

## Uso via API

### Endpoint REST

```bash
# Download direto do PDF
curl -X GET "http://localhost:8000/api/v1/sigef/memorial/999a354b-0c33-46a2-bfb3-28213892d541" \
  --output memorial.pdf
```

### Python Client
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/sigef/memorial/999a354b-0c33-46a2-bfb3-28213892d541"
)

if response.status_code == 200:
    with open("memorial.pdf", "wb") as f:
        f.write(response.content)
```

### JavaScript/TypeScript
```typescript
const response = await fetch(
  'http://localhost:8000/api/v1/sigef/memorial/999a354b-0c33-46a2-bfb3-28213892d541'
);

if (response.ok) {
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'memorial.pdf';
  link.click();
}
```

---

## Estrutura do Arquivo

O PDF gerado pelo SIGEF contém:

### Cabeçalho
- Logo do INCRA
- Título "MEMORIAL DESCRITIVO"
- Código da parcela
- Data de geração

### Seção 1: Identificação
- Denominação da parcela
- Município/UF
- Área total (ha)
- Perímetro (m)

### Seção 2: Responsável Técnico
- Nome e registro profissional
- CREA/CAU
- ART (Anotação de Responsabilidade Técnica)

### Seção 3: Vértices
Tabela com todos os vértices:
- Código do vértice
- Latitude/Longitude
- Coordenadas UTM
- Método de posicionamento
- Precisão (sigma)

### Seção 4: Limites
Tabela com os limites:
- Vértice inicial → final
- Azimute
- Distância
- Confrontante

### Rodapé
- Data e hora de geração
- Assinatura digital (quando aplicável)
- QR Code para validação

---

## Nomenclatura de Arquivos

Padrão: `{codigo}_memorial.pdf`

**Exemplo:**
```
999a354b-0c33-46a2-bfb3-28213892d541_memorial.pdf
```

---

## Testes

### Teste Manual
```bash
# 1. Autentique-se
curl -X POST http://localhost:8000/api/v1/auth/login

# 2. Baixe o memorial
curl -X GET "http://localhost:8000/api/v1/sigef/memorial/999a354b-0c33-46a2-bfb3-28213892d541" \
  --output memorial.pdf

# 3. Verifique o arquivo
file memorial.pdf
# Saída esperada: PDF document, version 1.x
```

### Teste Automatizado
```python
# tests/test_memorial.py

async def test_download_memorial(sigef_client, valid_session):
    codigo = "999a354b-0c33-46a2-bfb3-28213892d541"
    
    path = await sigef_client.download_memorial(
        codigo=codigo,
        session=valid_session,
    )
    
    assert path.exists()
    assert path.suffix == ".pdf"
    assert path.stat().st_size > 1000  # PDF não vazio
```

---

## Performance

| Métrica | Valor |
|---------|-------|
| Tempo médio | 2-5 segundos |
| Tamanho médio | 100-500 KB |
| Timeout | 60 segundos |
| Retry | 3 tentativas |

---

## Comparação com CSVs

| Tipo | Formato | Uso | Tamanho |
|------|---------|-----|---------|
| **CSVs** | Texto estruturado | Processamento automatizado | 5-50 KB |
| **Memorial** | PDF formatado | Documentação oficial | 100-500 KB |

**Quando usar cada um:**
- **CSVs**: Para análise de dados, importação em SIG, processamento em lote
- **Memorial**: Para documentação legal, processos oficiais, impressão

---

## Próximos Passos

Possíveis melhorias:
1. ✅ Download implementado
2. 🔄 Parse do PDF para extrair dados estruturados
3. 🔄 Geração de memorial customizado
4. 🔄 Validação de assinatura digital
5. 🔄 Comparação entre versões

---

## Referências

- [SIGEF INCRA](https://sigef.incra.gov.br)
- [Documentação API REST](../README.md)
- [Download CSV](03_download_csv_sigef.md)
- [Autenticação SIGEF](02_autenticacao_sigef.md)

---

*Implementado em Dezembro/2025*
