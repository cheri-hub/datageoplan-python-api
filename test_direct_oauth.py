"""
Teste: acessar diretamente a URL de OAuth do SIGEF
para ver se o redirecionamento funciona
"""

from playwright.sync_api import sync_playwright
import time


def test_direct_oauth():
    print("=" * 60)
    print("TESTE: OAuth direto do SIGEF")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Carrega com storage_state
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            storage_state="test_govbr_state.json"
        )
        page = context.new_page()
        
        # Acessa diretamente a URL de OAuth do SIGEF
        oauth_url = "https://sigef.incra.gov.br/oauth2/authorization/govbr"
        print(f"\nAcessando: {oauth_url}")
        
        page.goto(oauth_url)
        
        # Monitora redirecionamentos
        print("\nMonitorando redirecionamentos...")
        for i in range(60):
            time.sleep(1)
            url = page.url
            print(f"  [{i+1}s] {url}")
            
            # Se chegou no SIGEF (não na página OAuth)
            if "sigef.incra.gov.br" in url and "oauth2" not in url:
                print("\n✅ Sucesso! Redirecionado para SIGEF")
                break
            
            # Se ficou preso em servicos.acesso.gov.br
            if "servicos.acesso.gov.br" in url and i >= 5:
                print("\n⚠️ Preso em servicos.acesso.gov.br")
                print("Verificando se há algum parâmetro de redirect...")
                
                # Verifica query params
                print(f"URL completa: {url}")
                
                # Tenta voltar navegando
                print("\nTentando navegar diretamente para callback do SIGEF...")
                # O callback típico seria algo como /oauth2/callback ou /login/oauth2/code/govbr
                break
        
        # Mostra estado final
        print(f"\nURL final: {page.url}")
        
        # Captura cookies
        cookies = context.cookies()
        sigef_cookies = [c for c in cookies if 'sigef' in c.get('domain', '')]
        print(f"\nCookies SIGEF: {len(sigef_cookies)}")
        for c in sigef_cookies:
            print(f"  - {c['name']}: {c['value'][:30]}...")
        
        input("\n>>> Pressione ENTER para fechar...")
        browser.close()


if __name__ == "__main__":
    test_direct_oauth()
