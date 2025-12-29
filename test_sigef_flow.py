"""
Script de teste para o fluxo SIGEF.
Fluxo correto: SIGEF -> Entrar -> Gov.br (login) -> Redirecionado para SIGEF
"""

from playwright.sync_api import sync_playwright
import json
import time


def test_sigef_flow():
    print("=" * 60)
    print("TESTE DO FLUXO SIGEF")
    print("Fluxo: SIGEF -> Entrar -> Gov.br -> SIGEF")
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
        
        # PASSO 1: Acessa SIGEF
        print("\n[PASSO 1] Acessando SIGEF...")
        page.goto("https://sigef.incra.gov.br/")
        page.wait_for_load_state("networkidle")
        print(f"URL: {page.url}")
        
        # PASSO 2: Clica em "Entrar"
        print("\n[PASSO 2] Clicando em 'Entrar'...")
        
        # O botão é <button class="br-button sign-in small">Entrar</button>
        selectors = [
            "button.sign-in",
            "button:has-text('Entrar')",
            "text=Entrar",
        ]
        
        login_clicked = False
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    print(f"Botão encontrado com seletor: {sel}")
                    btn.click()
                    login_clicked = True
                    break
            except Exception as e:
                print(f"  Seletor {sel} falhou: {e}")
        
        if not login_clicked:
            print("Botão 'Entrar' não encontrado!")
        
        # PASSO 3: Aguarda redirecionamento para Gov.br e faz login
        print("\n[PASSO 3] Redirecionado para Gov.br...")
        page.wait_for_load_state("networkidle")
        print(f"URL: {page.url}")
        
        print("\n" + "=" * 60)
        print(">>> FAÇA LOGIN NO GOV.BR COM CERTIFICADO <<<")
        print("=" * 60)
        input("\n>>> Após completar o login, pressione ENTER...")
        
        # PASSO 4: Verifica se foi redirecionado de volta para SIGEF
        print("\n[PASSO 4] Verificando redirecionamento...")
        current_url = page.url
        print(f"URL atual: {current_url}")
        
        if "sigef.incra.gov.br" in current_url:
            print("✅ Redirecionado para SIGEF!")
        else:
            print("⚠️ Ainda não está no SIGEF. Aguardando...")
            for i in range(30):
                time.sleep(1)
                url = page.url
                print(f"  [{i+1}s] URL: {url}")
                if "sigef.incra.gov.br" in url:
                    print("✅ Redirecionado!")
                    break
        
        # Verifica se está logado
        final_url = page.url
        print(f"\nURL final: {final_url}")
        
        if page.locator("text=Sair").count() > 0:
            print("✅ LOGADO NO SIGEF!")
            
            # Salva o storage_state para uso futuro
            context.storage_state(path="sigef_authenticated_state.json")
            print("✅ Estado salvo em 'sigef_authenticated_state.json'")
        else:
            print("❌ Não parece estar logado")
        
        input("\n>>> Pressione ENTER para fechar...")
        browser.close()


if __name__ == "__main__":
    test_sigef_flow()
