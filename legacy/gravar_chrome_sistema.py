"""
Usa o Chrome instalado no sistema (não o Chromium do Playwright)
Isso permite acesso aos certificados A1 instalados no Windows
"""

from playwright.sync_api import sync_playwright
import os


def gravar_com_chrome_sistema():
    print("=" * 60)
    print("GRAVADOR COM CHROME DO SISTEMA")
    print("=" * 60)
    print("\n🔐 Usando certificados A1 instalados no Windows")
    print("=" * 60)
    
    input("\nPressione ENTER para abrir o Chrome...")
    
    with sync_playwright() as p:
        # Usa o Chrome instalado no sistema (channel="chrome")
        # Isso dá acesso aos certificados instalados no Windows
        browser = p.chromium.launch(
            channel="chrome",  # Usa Chrome do sistema, não Chromium do Playwright
            headless=False,    # Precisa ser visível para selecionar certificado
            args=[
                "--disable-blink-features=AutomationControlled",  # Evita detecção de bot
            ]
        )
        
        context = browser.new_context(
            ignore_https_errors=True  # Aceita certificados SSL
        )
        
        page = context.new_page()
        
        print("\n🌐 Navegando para gov.br...")
        page.goto("https://sso.acesso.gov.br")
        
        print("\n✅ Chrome aberto!")
        print("=" * 60)
        print("📝 INSTRUÇÕES:")
        print("1. Clique em 'Certificado Digital'")
        print("2. Selecione seu certificado A1 quando solicitado")
        print("3. Digite a senha do certificado se necessário")
        print("4. Após fazer login, volte aqui")
        print("=" * 60)
        
        input("\nPressione ENTER após completar o login...")
        
        # Captura informações
        print(f"\n📍 URL atual: {page.url}")
        
        # Salva o estado
        context.storage_state(path="auth_state.json")
        print("✅ Sessão salva em 'auth_state.json'!")
        
        # Salva o HTML da página logada
        try:
            with open("pagina_logada.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("✅ HTML salvo em 'pagina_logada.html'!")
        except Exception as e:
            print(f"⚠️ Erro ao salvar HTML: {e}")
        
        # Captura cookies
        cookies = context.cookies()
        print(f"✅ {len(cookies)} cookies capturados!")
        
        import json
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print("✅ Cookies salvos em 'cookies.json'!")
        
        browser.close()
        print("\n🎉 Gravação concluída!")


if __name__ == "__main__":
    gravar_com_chrome_sistema()
