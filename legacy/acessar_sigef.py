"""
Acessa o SIGEF INCRA usando autenticação Gov.br
"""

from playwright.sync_api import sync_playwright
import json
import time


def acessar_sigef():
    print("=" * 60)
    print("ACESSO AO SIGEF INCRA VIA GOV.BR")
    print("=" * 60)
    
    input("\nPressione ENTER para abrir o navegador...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Carrega o contexto com a sessão do Gov.br
        context = browser.new_context(
            storage_state="auth_state.json"
        )
        
        page = context.new_page()
        
        # Acessa o SIGEF
        print("\n🌐 Acessando SIGEF INCRA...")
        page.goto("https://sigef.incra.gov.br/")
        
        # Aguarda carregar
        page.wait_for_load_state("networkidle")
        
        print(f"📍 URL atual: {page.url}")
        print("\n✅ SIGEF aberto!")
        print("=" * 60)
        print("\n💡 INSTRUÇÕES:")
        print("1. Procure o botão 'Entrar com Gov.br' ou similar")
        print("2. Clique para iniciar o login")
        print("3. Se a sessão estiver válida, deve logar automaticamente")
        print("=" * 60)
        
        input("\nPressione ENTER após fazer o login para salvar a sessão do SIGEF...")
        
        # Salva o novo estado (com cookies do SIGEF)
        context.storage_state(path="auth_state_sigef.json")
        print("✅ Sessão do SIGEF salva em 'auth_state_sigef.json'!")
        
        # Captura cookies do SIGEF
        cookies = context.cookies()
        sigef_cookies = [c for c in cookies if 'sigef' in c.get('domain', '').lower() or 'incra' in c.get('domain', '').lower()]
        
        if sigef_cookies:
            with open("cookies_sigef.json", "w", encoding="utf-8") as f:
                json.dump(sigef_cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ {len(sigef_cookies)} cookies do SIGEF salvos em 'cookies_sigef.json'!")
        
        # Salva o HTML da página
        try:
            with open("pagina_sigef.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("✅ HTML da página salvo em 'pagina_sigef.html'!")
        except Exception as e:
            print(f"⚠️ Erro ao salvar HTML: {e}")
        
        print(f"\n📍 URL final: {page.url}")
        
        input("\nPressione ENTER para fechar o navegador...")
        
        browser.close()
        print("\n🎉 Concluído!")


if __name__ == "__main__":
    acessar_sigef()
