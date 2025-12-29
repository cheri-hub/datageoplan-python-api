"""
Teste: Login Gov.br + SIGEF na mesma sessão do navegador
Igual ao workflow manual do usuário
"""

from playwright.sync_api import sync_playwright
import time


def test_same_session():
    print("=" * 60)
    print("TESTE: Gov.br + SIGEF na mesma sessão")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        # PASSO 1: Acessa SIGEF primeiro
        print("\n[1] Acessando SIGEF...")
        page.goto("https://sigef.incra.gov.br/")
        page.wait_for_load_state("networkidle")
        print(f"URL: {page.url}")
        
        # PASSO 2: Clica em login Gov.br
        print("\n[2] Clicando em login Gov.br...")
        btn = page.locator("a:has-text('Gov.br')").first
        if btn.is_visible():
            btn.click()
        
        # PASSO 3: Aguarda redirecionamento para Gov.br
        print("\n[3] Aguardando redirecionamento para Gov.br...")
        page.wait_for_load_state("networkidle")
        print(f"URL: {page.url}")
        
        # PASSO 4: Usuário faz login manualmente
        print("\n" + "=" * 60)
        print(">>> FAÇA LOGIN COM CERTIFICADO DIGITAL <<<")
        print("=" * 60)
        input("\n>>> Após completar o login, pressione ENTER...")
        
        # PASSO 5: Verifica onde estamos
        current_url = page.url
        print(f"\nURL atual: {current_url}")
        
        if "sigef.incra.gov.br" in current_url:
            print("✅ Já está no SIGEF!")
        elif "servicos.acesso.gov.br" in current_url:
            print("⚠️ Está no portal Gov.br")
            print("O redirecionamento automático não ocorreu.")
            
            # Tenta navegar manualmente para o SIGEF OAuth
            print("\nTentando navegar para SIGEF OAuth...")
            page.goto("https://sigef.incra.gov.br/oauth2/authorization/govbr")
            page.wait_for_load_state("networkidle")
            
            # Aguarda
            for i in range(10):
                time.sleep(1)
                url = page.url
                print(f"  [{i+1}s] {url}")
                if "sigef.incra.gov.br" in url and "oauth2" not in url:
                    print("✅ Redirecionado!")
                    break
        
        # Estado final
        print(f"\nURL final: {page.url}")
        
        # Verifica login
        if page.locator("text=Sair").count() > 0:
            print("✅ LOGADO NO SIGEF!")
        
        # Salva estado para uso futuro
        context.storage_state(path="sigef_full_state.json")
        print("\nEstado completo salvo em 'sigef_full_state.json'")
        
        # Testa download
        print("\n" + "=" * 60)
        print("TESTANDO DOWNLOAD")
        print("=" * 60)
        
        test_parcela = "999a354b-0c33-46a2-bfb3-28213892d541"
        download_url = f"https://sigef.incra.gov.br/geo/exportar/parcela/csv/{test_parcela}/"
        
        print(f"Baixando: {download_url}")
        page.goto(download_url)
        page.wait_for_load_state("networkidle")
        
        content_type = page.evaluate("() => document.contentType")
        print(f"Content-Type: {content_type}")
        
        content = page.content()
        if "<!DOCTYPE html>" in content or "<html" in content.lower():
            print("❌ Recebeu HTML (provavelmente página de login)")
            print(content[:500])
        else:
            print("✅ Parece ser CSV!")
            print(content[:500])
        
        input("\n>>> Pressione ENTER para fechar...")
        browser.close()


if __name__ == "__main__":
    test_same_session()
