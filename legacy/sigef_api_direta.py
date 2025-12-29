"""
SIGEF - Download direto via API (sem navegador)
Usa as APIs mapeadas para baixar CSV diretamente
"""

import requests
import json
import os
from datetime import datetime


# Pasta para downloads
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads_sigef")

# URLs das APIs
APIS = {
    "parcela": "https://sigef.incra.gov.br/geo/exportar/parcela/csv/{codigo}/",
    "vertice": "https://sigef.incra.gov.br/geo/exportar/vertice/csv/{codigo}/",
    "limite": "https://sigef.incra.gov.br/geo/exportar/limite/csv/{codigo}/",
}

# Headers padrão (baseado no mapeamento)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "upgrade-insecure-requests": "1",
}


def carregar_cookies():
    """Carrega cookies da sessão salva"""
    try:
        with open("auth_state_sigef.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        cookies = {}
        for cookie in data.get("cookies", []):
            # Filtra cookies relevantes (SIGEF e Gov.br)
            domain = cookie.get("domain", "")
            if "sigef" in domain or "incra" in domain:
                cookies[cookie["name"]] = cookie["value"]
        
        return cookies
    except FileNotFoundError:
        print("❌ Arquivo auth_state_sigef.json não encontrado!")
        print("Execute primeiro: python acessar_sigef.py")
        return None


def baixar_csv(codigo_parcela: str, tipo: str, session: requests.Session) -> str:
    """
    Baixa um CSV específico da parcela
    
    Args:
        codigo_parcela: UUID da parcela
        tipo: 'parcela', 'vertice' ou 'limite'
        session: Sessão requests com cookies
    
    Returns:
        Caminho do arquivo salvo ou None se falhar
    """
    url = APIS[tipo].format(codigo=codigo_parcela)
    
    # Header referer específico
    headers = HEADERS.copy()
    headers["referer"] = f"https://sigef.incra.gov.br/geo/parcela/detalhe/{codigo_parcela}/"
    
    print(f"\n📥 Baixando {tipo}...")
    print(f"   URL: {url}")
    
    try:
        response = session.get(url, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            # Verifica se é realmente um CSV
            content_type = response.headers.get("content-type", "")
            
            if "text/csv" in content_type or "octet-stream" in content_type or response.text.startswith(("codigo", "CODIGO", '"')):
                # Salva o arquivo
                filename = f"{codigo_parcela[:8]}_{tipo}.csv"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                print(f"   ✅ Salvo: {filename}")
                return filepath
            else:
                print(f"   ⚠️ Resposta não é CSV. Pode ser página de login.")
                # Salva para debug
                debug_file = os.path.join(DOWNLOAD_DIR, f"debug_{tipo}.html")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"   📝 Debug salvo: debug_{tipo}.html")
                return None
        
        elif response.status_code == 302 or response.status_code == 301:
            print(f"   ⚠️ Redirecionamento para: {response.headers.get('Location', 'N/A')}")
            print("   Sessão pode ter expirado!")
            return None
        
        else:
            print(f"   ❌ Erro: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erro de conexão: {e}")
        return None


def baixar_todos_csv(codigo_parcela: str):
    """Baixa todos os CSVs de uma parcela"""
    print("=" * 60)
    print("SIGEF - DOWNLOAD DIRETO VIA API")
    print("=" * 60)
    
    # Cria pasta de downloads
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Carrega cookies
    cookies = carregar_cookies()
    if not cookies:
        return
    
    print(f"\n🍪 Cookies carregados: {len(cookies)}")
    for name in cookies:
        print(f"   - {name}")
    
    # Cria sessão com cookies
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain="sigef.incra.gov.br")
    
    print(f"\n🔍 Parcela: {codigo_parcela}")
    
    # Baixa cada tipo
    resultados = {}
    for tipo in ["parcela", "vertice", "limite"]:
        filepath = baixar_csv(codigo_parcela, tipo, session)
        resultados[tipo] = filepath
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    sucesso = sum(1 for v in resultados.values() if v)
    print(f"\n✅ {sucesso}/3 arquivos baixados com sucesso")
    
    for tipo, filepath in resultados.items():
        if filepath:
            # Mostra preview do arquivo
            print(f"\n📄 {tipo.upper()}:")
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                print(f"   Linhas: {len(lines)}")
                if lines:
                    print(f"   Header: {lines[0].strip()[:80]}...")
    
    print(f"\n📁 Arquivos em: {DOWNLOAD_DIR}")
    
    return resultados


def testar_sessao():
    """Testa se a sessão ainda é válida fazendo um download de teste"""
    print("=" * 60)
    print("TESTE DE SESSÃO")
    print("=" * 60)
    
    cookies = carregar_cookies()
    if not cookies:
        return False
    
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain="sigef.incra.gov.br")
    
    # Testa fazendo download de uma parcela conhecida (pública)
    # Parcela de teste
    codigo_teste = "999a354b-0c33-46a2-bfb3-28213892d541"
    url = f"https://sigef.incra.gov.br/geo/exportar/parcela/csv/{codigo_teste}/"
    
    print(f"\n🔍 Testando download de parcela...")
    print(f"   URL: {url}")
    
    headers = HEADERS.copy()
    headers["referer"] = f"https://sigef.incra.gov.br/geo/parcela/detalhe/{codigo_teste}/"
    
    response = session.get(url, headers=headers, allow_redirects=False)
    
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
    
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        if "text/csv" in content_type:
            print("\n✅ Sessão válida! Download funcionando.")
            # Mostra preview
            lines = response.text.split("\n")
            print(f"   Linhas: {len(lines)}")
            print(f"   Header: {lines[0][:60]}...")
            return True
        else:
            print("\n⚠️ Resposta não é CSV - Sessão pode ter expirado")
            return False
    elif response.status_code == 302:
        print(f"\n⚠️ Redirecionamento - Sessão expirada!")
        print(f"   Location: {response.headers.get('Location', 'N/A')}")
        return False
    else:
        print(f"\n⚠️ Status inesperado: {response.status_code}")
        return False


if __name__ == "__main__":
    print("\n🌿 SIGEF - Download via API")
    print("=" * 60)
    print("1. Baixar CSVs de uma parcela")
    print("2. Testar se a sessão é válida")
    print("=" * 60)
    
    opcao = input("\nEscolha (1 ou 2): ").strip()
    
    if opcao == "2":
        testar_sessao()
    else:
        codigo = input("\n🔍 Código da parcela: ").strip()
        if codigo:
            baixar_todos_csv(codigo)
        else:
            # Usa o código do teste anterior
            codigo = "999a354b-0c33-46a2-bfb3-28213892d541"
            print(f"Usando código de teste: {codigo}")
            baixar_todos_csv(codigo)
