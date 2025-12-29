"""
Debugar a página /oauth2/authorization/govbr
"""

from playwright.sync_api import sync_playwright
import time


def debug_oauth_page():
    print("=" * 60)
    print("DEBUG: Página OAuth do SIGEF")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            storage_state="test_govbr_state.json"
        )
        
        # Intercepta requests
        def log_request(request):
            if "sigef" in request.url or "gov.br" in request.url:
                print(f"  📤 {request.method} {request.url}")
        
        def log_response(response):
            if "sigef" in response.url or "gov.br" in response.url:
                print(f"  📥 {response.status} {response.url}")
        
        page = context.new_page()
        page.on("request", log_request)
        page.on("response", log_response)
        
        # Acessa a página OAuth
        print("\nAcessando /oauth2/authorization/govbr...")
        print("Requests/Responses:")
        
        response = page.goto("https://sigef.incra.gov.br/oauth2/authorization/govbr", wait_until="domcontentloaded")
        
        print(f"\nResponse status: {response.status}")
        print(f"Response URL: {response.url}")
        
        # Headers
        headers = response.headers
        print(f"\nHeaders importantes:")
        for key in ["location", "set-cookie", "content-type"]:
            if key in headers:
                print(f"  {key}: {headers[key][:100]}")
        
        # Aguarda um pouco
        time.sleep(2)
        
        print(f"\nURL atual: {page.url}")
        print(f"\nConteúdo da página:")
        print(page.content()[:2000])
        
        input("\n>>> Pressione ENTER para fechar...")
        browser.close()


if __name__ == "__main__":
    debug_oauth_page()
