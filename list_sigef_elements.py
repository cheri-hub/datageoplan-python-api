"""
Lista todos os elementos clicáveis na página SIGEF
"""

from playwright.sync_api import sync_playwright


def list_elements():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        page.goto("https://sigef.incra.gov.br/")
        page.wait_for_load_state("networkidle")
        
        print("=" * 60)
        print("ELEMENTOS NA PÁGINA SIGEF")
        print("=" * 60)
        
        # Lista todos os links
        print("\n📎 LINKS (tag <a>):")
        links = page.locator("a").all()
        for i, link in enumerate(links):
            try:
                href = link.get_attribute("href") or ""
                text = link.text_content().strip()
                classes = link.get_attribute("class") or ""
                if text or href:
                    print(f"  {i+1}. texto='{text[:40]}' href='{href[:50]}' class='{classes[:30]}'")
            except:
                pass
        
        # Lista todos os botões
        print("\n🔘 BOTÕES (tag <button>):")
        buttons = page.locator("button").all()
        for i, btn in enumerate(buttons):
            try:
                text = btn.text_content().strip()
                classes = btn.get_attribute("class") or ""
                print(f"  {i+1}. texto='{text[:40]}' class='{classes[:30]}'")
            except:
                pass
        
        # Procura elementos com "entrar" ou "login"
        print("\n🔍 ELEMENTOS COM 'entrar' ou 'login':")
        elements = page.locator("text=/entrar|login/i").all()
        for i, el in enumerate(elements):
            try:
                tag = el.evaluate("el => el.tagName")
                text = el.text_content().strip()[:50]
                href = el.get_attribute("href") or ""
                print(f"  {i+1}. <{tag}> texto='{text}' href='{href}'")
            except:
                pass
        
        input("\n>>> Pressione ENTER para fechar...")
        browser.close()


if __name__ == "__main__":
    list_elements()
