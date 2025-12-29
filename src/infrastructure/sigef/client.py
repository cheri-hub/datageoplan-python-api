"""
Cliente SIGEF INCRA usando requisições HTTP diretas.

Implementação de alta performance que usa httpx para
fazer download de CSVs diretamente via API, sem browser.

NOTA: A autenticação inicial requer Playwright para
completar o fluxo OAuth Gov.br -> SIGEF.
"""

import asyncio
import concurrent.futures
import re
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.exceptions import (
    InvalidParcelaCodeError,
    ParcelaNotFoundError,
    SessionExpiredError,
    SigefError,
)
from src.core.logging import get_logger
from src.domain.entities import Cookie, Parcela, Session, TipoExportacao
from src.domain.interfaces import ISigefClient

logger = get_logger(__name__)

# Regex para validar código de parcela SIGEF
PARCELA_CODE_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# ThreadPoolExecutor para Playwright
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="sigef-playwright")


class HttpSigefClient(ISigefClient):
    """
    Cliente SIGEF que usa requisições HTTP diretas.
    
    Mais eficiente que usar browser para downloads,
    permite execução em modo headless e paralelo.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = str(self.settings.sigef_base_url).rstrip("/")
    
    def _validate_parcela_code(self, codigo: str) -> str:
        """Valida e normaliza código de parcela."""
        codigo = codigo.strip().lower()
        
        if not PARCELA_CODE_PATTERN.match(codigo):
            raise InvalidParcelaCodeError(codigo)
        
        return codigo
    
    def _build_cookies_dict(self, session: Session) -> dict[str, str]:
        """Constrói dicionário de cookies para requisições."""
        cookies = session.get_cookies_dict("all")
        
        if not cookies:
            raise SessionExpiredError("Sessão não possui cookies válidos.")
        
        return cookies
    
    def _get_headers(self) -> dict[str, str]:
        """Retorna headers padrão para requisições."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/csv,text/plain,*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{self.base_url}/",
        }
    
    async def authenticate(self, govbr_session: Session) -> Session:
        """
        Autentica no SIGEF usando sessão do Gov.br via Playwright.
        
        Usa browser para completar fluxo OAuth Gov.br -> SIGEF,
        capturando todos os cookies necessários.
        """
        if not govbr_session.is_govbr_authenticated:
            raise SigefError("Sessão Gov.br não está autenticada.")
        
        logger.info("Autenticando no SIGEF com sessão Gov.br (via browser)")
        
        # Executa em thread separada para evitar problemas com event loop
        loop = asyncio.get_event_loop()
        updated_session = await loop.run_in_executor(
            _executor,
            self._authenticate_sigef_sync,
            govbr_session,
        )
        
        return updated_session
    
    def _authenticate_sigef_sync(self, govbr_session: Session) -> Session:
        """
        Autenticação síncrona no SIGEF via Playwright.
        
        Fluxo igual ao legacy:
        1. Carrega contexto com storage_state do Gov.br (cookies + localStorage completo)
        2. Acessa página inicial do SIGEF
        3. Clica no botão "Entrar com Gov.br"
        4. Gov.br reconhece automaticamente e redireciona de volta
        5. SIGEF cria sessão e define cookies
        """
        import os
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=False,  # Precisa ser visível para OAuth
                args=["--disable-blink-features=AutomationControlled"],
            )
            
            try:
                # Usa storage_state se disponível (igual ao legacy!)
                if govbr_session.storage_state_path and os.path.exists(govbr_session.storage_state_path):
                    logger.info(f"Carregando storage_state de: {govbr_session.storage_state_path}")
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        storage_state=govbr_session.storage_state_path,
                    )
                else:
                    # Fallback: cria contexto e adiciona cookies manualmente
                    logger.warning("storage_state não disponível, usando cookies manualmente")
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 800},
                    )
                    
                    # Adiciona cookies do Gov.br ao contexto
                    playwright_cookies = []
                    for cookie in govbr_session.govbr_cookies:
                        playwright_cookies.append({
                            "name": cookie.name,
                            "value": cookie.value,
                            "domain": cookie.domain,
                            "path": cookie.path or "/",
                            "secure": cookie.secure,
                            "httpOnly": cookie.http_only,
                        })
                    
                    if playwright_cookies:
                        context.add_cookies(playwright_cookies)
                        logger.info(f"Adicionados {len(playwright_cookies)} cookies do Gov.br ao contexto")
                
                page = context.new_page()
                
                # PASSO 1: Acessa página inicial do SIGEF
                logger.info("Acessando página inicial do SIGEF")
                page.goto(f"{self.base_url}/", wait_until="networkidle", timeout=60000)
                
                current_url = page.url
                logger.info(f"URL após carregar SIGEF: {current_url}")
                
                # PASSO 2: Procura e clica no botão de login Gov.br
                logger.info("Procurando botão de login...")
                login_clicked = False
                
                # Seletores para o botão Entrar
                # O botão é: <button class="br-button sign-in small">Entrar</button>
                login_selectors = [
                    "button.sign-in",
                    "button:has-text('Entrar')",
                    "text=Entrar",
                    "a[href*='oauth']",
                ]
                
                for selector in login_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            logger.info(f"Encontrado botão: {selector}")
                            btn.click()
                            login_clicked = True
                            break
                    except Exception:
                        continue
                
                if not login_clicked:
                    # Se não encontrou botão, pode ser que já está logado
                    # ou o layout mudou - tenta acessar uma página autenticada
                    logger.warning("Botão de login não encontrado, verificando se já está logado...")
                    if page.locator("text=Sair").count() > 0:
                        logger.info("Já está logado no SIGEF!")
                    else:
                        logger.warning("Não encontrou botão de login nem indicação de estar logado")
                
                # PASSO 3: Aguarda fluxo OAuth completar
                # O fluxo vai: SIGEF -> Gov.br -> (autorização) -> SIGEF (callback)
                logger.info("Aguardando fluxo OAuth...")
                
                # Aguarda até não estar mais no Gov.br
                max_wait = 45  # segundos
                waited = 0
                while waited < max_wait:
                    page.wait_for_timeout(1000)
                    waited += 1
                    current_url = page.url
                    
                    # Se voltou para o SIGEF, o fluxo completou
                    if "sigef.incra.gov.br" in current_url and "oauth2" not in current_url:
                        logger.info(f"Redirecionado de volta ao SIGEF: {current_url}")
                        break
                    
                    # Se está em servicos.acesso.gov.br - página de autorização OAuth
                    # Precisa clicar em "Autorizar" ou similar
                    if "servicos.acesso.gov.br" in current_url:
                        logger.info(f"Página de autorização Gov.br detectada: {current_url}")
                        
                        # Tenta encontrar e clicar no botão de autorizar
                        auth_selectors = [
                            "button:has-text('Autorizar')",
                            "button:has-text('Permitir')",
                            "button:has-text('Continuar')",
                            "button:has-text('Confirmar')",
                            "input[type='submit']",
                            "button[type='submit']",
                            ".btn-primary",
                            "a:has-text('Autorizar')",
                            "a:has-text('Continuar')",
                        ]
                        
                        for selector in auth_selectors:
                            try:
                                btn = page.locator(selector).first
                                if btn.is_visible(timeout=1000):
                                    logger.info(f"Clicando em botão de autorização: {selector}")
                                    btn.click()
                                    page.wait_for_timeout(2000)
                                    break
                            except Exception:
                                continue
                    
                    # Se está em página de login Gov.br, sessão expirou
                    if any(x in current_url for x in ["sso.acesso.gov.br/login", "/authorize"]):
                        if page.locator("text=Certificado Digital").count() > 0 or \
                           page.locator("input[type='password']").count() > 0:
                            logger.warning("Sessão Gov.br expirada - página de login detectada")
                            raise SessionExpiredError("Sessão Gov.br expirada. Necessário novo login.")
                    
                    logger.debug(f"Aguardando... URL atual: {current_url}")
                
                # Aguarda página final carregar
                page.wait_for_load_state("networkidle", timeout=10000)
                
                final_url = page.url
                logger.info(f"URL final: {final_url}")
                
                # Captura todos os cookies
                all_cookies = context.cookies()
                
                logger.info(f"Total de cookies capturados: {len(all_cookies)}")
                for c in all_cookies:
                    logger.debug(f"Cookie: {c['name']} @ {c.get('domain', '')}")
                
                sigef_cookies = []
                govbr_updated_cookies = []
                
                for c in all_cookies:
                    domain = c.get("domain", "")
                    cookie_obj = Cookie(
                        name=c["name"],
                        value=c["value"],
                        domain=domain,
                        path=c.get("path", "/"),
                        expires=c.get("expires"),
                        http_only=c.get("httpOnly", False),
                        secure=c.get("secure", False),
                        same_site=c.get("sameSite", "Lax"),
                    )
                    
                    if "sigef" in domain or "incra" in domain:
                        sigef_cookies.append(cookie_obj)
                    elif "gov.br" in domain or "acesso" in domain:
                        govbr_updated_cookies.append(cookie_obj)
                
                logger.info(f"Cookies SIGEF: {len(sigef_cookies)}, Gov.br: {len(govbr_updated_cookies)}")
                
                # Atualiza cookies do Gov.br também (podem ter sido renovados)
                if govbr_updated_cookies:
                    govbr_session.govbr_cookies = govbr_updated_cookies
                
                # Atualiza sessão
                govbr_session.sigef_cookies = sigef_cookies
                govbr_session.is_sigef_authenticated = len(sigef_cookies) > 0
                govbr_session.touch()
                
                return govbr_session
                
            finally:
                browser.close()
    
    async def get_parcela(self, codigo: str, session: Session) -> Parcela:
        """
        Obtém dados básicos de uma parcela.
        
        Por enquanto retorna apenas estrutura básica.
        Dados completos viriam de parsing do HTML ou outra API.
        """
        codigo = self._validate_parcela_code(codigo)
        
        cookies = self._build_cookies_dict(session)
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            cookies=cookies,
            headers=self._get_headers(),
        ) as client:
            url = f"{self.base_url}/geo/parcela/detalhe/{codigo}/"
            response = await client.get(url)
            
            if response.status_code == 404:
                raise ParcelaNotFoundError(codigo)
            
            if response.status_code != 200:
                raise SigefError(
                    f"Erro ao buscar parcela: HTTP {response.status_code}"
                )
            
            # Retorna parcela básica
            # TODO: Implementar parsing do HTML para extrair mais dados
            return Parcela(codigo=codigo)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def download_csv(
        self,
        codigo: str,
        tipo: TipoExportacao,
        session: Session,
        destino: Path | None = None,
    ) -> Path:
        """
        Baixa CSV de uma parcela.
        
        Usa retry automático com backoff exponencial
        para lidar com falhas temporárias.
        """
        codigo = self._validate_parcela_code(codigo)
        
        # Monta URL de download
        url = f"{self.base_url}/geo/exportar/{tipo.value}/csv/{codigo}/"
        
        logger.info(
            "Baixando CSV",
            tipo=tipo.value,
            codigo=codigo,
        )
        
        cookies = self._build_cookies_dict(session)
        
        # Headers com Referer específico da parcela (importante para SIGEF)
        headers = self._get_headers()
        headers["Referer"] = f"{self.base_url}/geo/parcela/detalhe/{codigo}/"
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60.0,
            cookies=cookies,
            headers=headers,
        ) as client:
            response = await client.get(url)
            
            if response.status_code == 404:
                raise ParcelaNotFoundError(codigo)
            
            if response.status_code == 401:
                raise SessionExpiredError(
                    "Sessão expirada. Faça login novamente."
                )
            
            if response.status_code != 200:
                raise SigefError(
                    f"Erro ao baixar CSV: HTTP {response.status_code}"
                )
            
            # Verifica se é realmente um CSV
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                # Provavelmente redirecionou para login
                raise SessionExpiredError(
                    "Sessão inválida. Recebido HTML ao invés de CSV."
                )
            
            # Define destino
            if destino is None:
                downloads_dir = self.settings.downloads_dir
                downloads_dir.mkdir(parents=True, exist_ok=True)
                
                # Nome: codigo_tipo.csv
                filename = f"{codigo}_{tipo.value}.csv"
                destino = downloads_dir / filename
            
            # Salva arquivo
            destino.write_bytes(response.content)
            
            logger.info(
                "CSV baixado com sucesso",
                tipo=tipo.value,
                destino=str(destino),
                tamanho_bytes=len(response.content),
            )
            
            return destino
    
    async def download_all_csvs(
        self,
        codigo: str,
        session: Session,
        destino_dir: Path | None = None,
    ) -> dict[TipoExportacao, Path]:
        """
        Baixa todos os CSVs de uma parcela.
        
        Faz downloads em sequência para evitar rate limiting.
        """
        codigo = self._validate_parcela_code(codigo)
        destino_dir = destino_dir or self.settings.downloads_dir
        destino_dir.mkdir(parents=True, exist_ok=True)
        
        results: dict[TipoExportacao, Path] = {}
        
        for tipo in TipoExportacao:
            destino = destino_dir / f"{codigo}_{tipo.value}.csv"
            
            try:
                path = await self.download_csv(
                    codigo=codigo,
                    tipo=tipo,
                    session=session,
                    destino=destino,
                )
                results[tipo] = path
            except Exception as e:
                logger.error(
                    "Falha ao baixar CSV",
                    tipo=tipo.value,
                    codigo=codigo,
                    error=str(e),
                )
                raise
        
        logger.info(
            "Todos os CSVs baixados",
            codigo=codigo,
            arquivos=len(results),
        )
        
        return results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def download_memorial(
        self,
        codigo: str,
        session: Session,
        destino: Path | None = None,
    ) -> Path:
        """
        Baixa memorial descritivo (PDF) de uma parcela.
        
        URL: /geo/parcela/memorial/{codigo}/
        """
        codigo = self._validate_parcela_code(codigo)
        
        # Monta URL de download do memorial
        url = f"{self.base_url}/geo/parcela/memorial/{codigo}/"
        
        logger.info(
            "Baixando memorial descritivo",
            codigo=codigo,
        )
        
        cookies = self._build_cookies_dict(session)
        
        # Headers com Referer específico da parcela (importante para SIGEF)
        headers = self._get_headers()
        headers["Referer"] = f"{self.base_url}/geo/parcela/detalhe/{codigo}/"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*"
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60.0,
            cookies=cookies,
            headers=headers,
        ) as client:
            response = await client.get(url)
            
            if response.status_code == 404:
                raise ParcelaNotFoundError(codigo)
            
            if response.status_code == 401:
                raise SessionExpiredError(
                    "Sessão expirada. Faça login novamente."
                )
            
            if response.status_code != 200:
                raise SigefError(
                    f"Erro ao baixar memorial: HTTP {response.status_code}"
                )
            
            # Verifica se é um PDF
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type and "application/pdf" not in content_type:
                # Provavelmente redirecionou para login
                raise SessionExpiredError(
                    "Sessão inválida. Recebido HTML ao invés de PDF."
                )
            
            # Define destino
            if destino is None:
                downloads_dir = self.settings.downloads_dir
                downloads_dir.mkdir(parents=True, exist_ok=True)
                
                # Nome: codigo_memorial.pdf
                filename = f"{codigo}_memorial.pdf"
                destino = downloads_dir / filename
            
            # Salva arquivo
            destino.write_bytes(response.content)
            
            logger.info(
                "Memorial descritivo baixado com sucesso",
                destino=str(destino),
                tamanho_bytes=len(response.content),
            )
            
            return destino
