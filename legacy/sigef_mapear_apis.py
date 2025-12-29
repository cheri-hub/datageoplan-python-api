"""
Intercepta e mapeia todas as chamadas de API do SIGEF
para identificar as URLs de download CSV
"""

from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime


# Pasta para logs
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs_api")


def interceptar_apis(codigo_parcela: str = None):
    print("=" * 60)
    print("SIGEF - MAPEAMENTO DE APIs")
    print("=" * 60)
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    if not codigo_parcela:
        codigo_parcela = input("\n🔍 Digite o código da parcela: ").strip()
    
    # Listas para armazenar requisições
    todas_requisicoes = []
    requisicoes_download = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            storage_state="auth_state_sigef.json",
            accept_downloads=True
        )
        
        page = context.new_page()
        
        # Intercepta TODAS as requisições
        def on_request(request):
            req_data = {
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
                "post_data": request.post_data,
                "resource_type": request.resource_type,
            }
            todas_requisicoes.append(req_data)
            
            # Filtra requisições interessantes (APIs, downloads)
            url = request.url.lower()
            if any(kw in url for kw in ['csv', 'export', 'download', 'api', 'parcela', 'vertice', 'limite', 'json']):
                print(f"🔗 {request.method} {request.url[:100]}")
                requisicoes_download.append(req_data)
        
        # Intercepta respostas
        def on_response(response):
            url = response.url.lower()
            content_type = response.headers.get('content-type', '')
            
            # Identifica downloads e APIs de dados
            if any(kw in url for kw in ['csv', 'export', 'download']) or \
               any(kw in content_type for kw in ['csv', 'json', 'octet-stream']):
                print(f"📥 [{response.status}] {response.url[:80]}")
                print(f"    Content-Type: {content_type}")
        
        page.on("request", on_request)
        page.on("response", on_response)
        
        print("\n🌐 Acessando SIGEF...")
        page.goto("https://sigef.incra.gov.br/")
        page.wait_for_load_state("networkidle")
        
        if codigo_parcela:
            print(f"\n🔍 Acessando parcela: {codigo_parcela}")
            url_parcela = f"https://sigef.incra.gov.br/geo/parcela/detalhe/{codigo_parcela}/"
            page.goto(url_parcela)
            page.wait_for_load_state("networkidle")
        
        print("\n" + "=" * 60)
        print("MONITORANDO REQUISIÇÕES")
        print("=" * 60)
        print("Clique nos botões de download CSV no navegador.")
        print("Todas as chamadas de API serão registradas.")
        print("=" * 60)
        
        input("\nPressione ENTER quando terminar de testar...")
        
        browser.close()
    
    # Salva logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Log completo
    log_completo = os.path.join(LOG_DIR, f"todas_requisicoes_{timestamp}.json")
    with open(log_completo, "w", encoding="utf-8") as f:
        json.dump(todas_requisicoes, f, indent=2, ensure_ascii=False, default=str)
    
    # Log filtrado (downloads/APIs)
    log_downloads = os.path.join(LOG_DIR, f"apis_download_{timestamp}.json")
    with open(log_downloads, "w", encoding="utf-8") as f:
        json.dump(requisicoes_download, f, indent=2, ensure_ascii=False, default=str)
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DAS APIs ENCONTRADAS")
    print("=" * 60)
    
    # Agrupa por padrão de URL
    apis_unicas = {}
    for req in requisicoes_download:
        # Extrai padrão da URL (remove IDs específicos)
        url = req["url"]
        # Simplifica URL para identificar padrão
        padrao = url.split("?")[0]  # Remove query string para agrupar
        if padrao not in apis_unicas:
            apis_unicas[padrao] = {
                "method": req["method"],
                "url_exemplo": url,
                "headers": req["headers"],
                "count": 0
            }
        apis_unicas[padrao]["count"] += 1
    
    print(f"\n📊 {len(todas_requisicoes)} requisições totais")
    print(f"📥 {len(requisicoes_download)} requisições de download/API")
    print(f"🔗 {len(apis_unicas)} endpoints únicos\n")
    
    for padrao, info in apis_unicas.items():
        print(f"\n{'='*60}")
        print(f"📌 Endpoint: {padrao}")
        print(f"   Método: {info['method']}")
        print(f"   Chamadas: {info['count']}x")
        print(f"   URL completa: {info['url_exemplo']}")
    
    # Salva resumo
    resumo_path = os.path.join(LOG_DIR, f"resumo_apis_{timestamp}.json")
    with open(resumo_path, "w", encoding="utf-8") as f:
        json.dump(apis_unicas, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n\n📁 Logs salvos em: {LOG_DIR}")
    print(f"   - todas_requisicoes_{timestamp}.json")
    print(f"   - apis_download_{timestamp}.json")
    print(f"   - resumo_apis_{timestamp}.json")
    
    return apis_unicas


if __name__ == "__main__":
    interceptar_apis()
