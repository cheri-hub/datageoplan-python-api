"""
Script para investigar a página servicos.acesso.gov.br
"""

from playwright.sync_api import sync_playwright
import time


def investigate_servicos():
    print("=" * 60)
    print("INVESTIGANDO servicos.acesso.gov.br")
    print("=" * 60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Carrega com storage_state do teste anterior
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            storage_state="test_govbr_state.json"
        )
        page = context.new_page()
        
        # Acessa SIGEF e inicia OAuth
        print("Acessando SIGEF...")
        page.goto("https://sigef.incra.gov.br/")
        page.wait_for_load_state("networkidle")
        
        # Clica no login Gov.br
        print("Clicando em login Gov.br...")
        btn = page.locator("a:has-text('Gov.br')").first
        if btn.is_visible():
            btn.click()
            page.wait_for_load_state("networkidle")
        
        time.sleep(3)
        
        # Agora estamos em servicos.acesso.gov.br
        print(f"\nURL: {page.url}")
        print("\n" + "=" * 60)
        print("ANALISANDO PÁGINA")
        print("=" * 60)
        
        # Lista todos os links
        print("\n📎 Links na página:")
        links = page.locator("a").all()
        for i, link in enumerate(links[:20]):  # Primeiros 20
            try:
                href = link.get_attribute("href")
                text = link.text_content().strip()[:50]
                print(f"  {i+1}. [{text}] -> {href}")
            except:
                pass
        
        # Lista todos os botões
        print("\n🔘 Botões na página:")
        buttons = page.locator("button").all()
        for i, btn in enumerate(buttons[:10]):
            try:
                text = btn.text_content().strip()[:50]
                print(f"  {i+1}. {text}")
            except:
                pass
        
        # Procura elementos com SIGEF ou INCRA
        print("\n🔍 Elementos com 'SIGEF' ou 'INCRA':")
        sigef_elements = page.locator("text=/sigef|incra/i").all()
        for i, el in enumerate(sigef_elements[:10]):
            try:
                tag = el.evaluate("el => el.tagName")
                text = el.text_content().strip()[:80]
                print(f"  {i+1}. <{tag}> {text}")
            except:
                pass
        
        # Procura por "autorizar", "continuar", "permitir"
        print("\n🔍 Elementos de autorização:")
        auth_elements = page.locator("text=/autorizar|continuar|permitir|confirmar/i").all()
        for i, el in enumerate(auth_elements[:10]):
            try:
                tag = el.evaluate("el => el.tagName")
                text = el.text_content().strip()[:80]
                print(f"  {i+1}. <{tag}> {text}")
            except:
                pass
        
        # Verifica iframes
        print("\n📦 Iframes:")
        iframes = page.locator("iframe").all()
        print(f"  Total: {len(iframes)}")
        
        input("\n>>> Investigue manualmente e pressione ENTER...")
        
        browser.close()


if __name__ == "__main__":
    investigate_servicos()
