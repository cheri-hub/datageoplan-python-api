"""
Serviço de Autenticação.

Orquestra o fluxo de autenticação Gov.br e SIGEF,
gerenciando sessões e validações.
"""

from src.core.exceptions import SessionExpiredError
from src.core.logging import get_logger
from src.domain.entities import Session
from src.domain.interfaces import IGovBrAuthenticator, ISessionRepository, ISigefClient

logger = get_logger(__name__)


class AuthService:
    """
    Serviço de autenticação seguindo princípios SOLID.
    
    - Single Responsibility: Apenas orquestra autenticação
    - Open/Closed: Extensível via novas implementações das interfaces
    - Liskov Substitution: Usa abstrações, não implementações
    - Interface Segregation: Interfaces específicas por responsabilidade
    - Dependency Inversion: Depende de abstrações injetadas
    """
    
    def __init__(
        self,
        govbr_authenticator: IGovBrAuthenticator,
        sigef_client: ISigefClient,
        session_repository: ISessionRepository,
    ):
        """
        Inicializa serviço com dependências injetadas.
        
        Args:
            govbr_authenticator: Implementação de autenticação Gov.br
            sigef_client: Cliente SIGEF
            session_repository: Repositório de sessões
        """
        self.govbr = govbr_authenticator
        self.sigef = sigef_client
        self.sessions = session_repository
    
    async def get_or_create_session(self, force_new: bool = False) -> Session:
        """
        Obtém sessão existente válida ou cria nova.
        
        Args:
            force_new: Se True, sempre cria nova sessão.
        
        Returns:
            Sessão autenticada no Gov.br e SIGEF.
        """
        if not force_new:
            # Tenta carregar sessão existente
            session = await self.sessions.load_latest()
            
            if session and session.is_valid():
                logger.info(
                    "Usando sessão existente",
                    session_id=session.session_id,
                    cpf=session.cpf,
                )
                
                # Valida se ainda funciona
                if await self.govbr.validate_session(session):
                    session.touch()
                    await self.sessions.save(session)
                    return session
                
                logger.info("Sessão existente inválida, criando nova")
        
        # Cria nova sessão
        return await self.create_new_session()
    
    async def create_new_session(self) -> Session:
        """
        Cria nova sessão autenticada.
        
        Fluxo:
        1. Autentica no Gov.br (interativo com certificado)
        2. Usa sessão Gov.br para autenticar no SIGEF
        3. Persiste sessão combinada
        
        Returns:
            Sessão autenticada em ambas plataformas.
        """
        logger.info("Iniciando nova autenticação")
        
        # 1. Gov.br
        session = await self.govbr.authenticate(headless=False)
        logger.info("Gov.br autenticado", cpf=session.cpf)
        
        # 2. SIGEF
        session = await self.sigef.authenticate(session)
        logger.info("SIGEF autenticado")
        
        # 3. Persiste
        await self.sessions.save(session)
        logger.info("Sessão persistida", session_id=session.session_id)
        
        return session
    
    async def validate_current_session(self) -> tuple[bool, Session | None]:
        """
        Valida a sessão atual.
        
        Returns:
            Tupla (is_valid, session). Session é None se inválida.
        """
        session = await self.sessions.load_latest()
        
        if not session:
            return False, None
        
        if session.is_expired():
            logger.info("Sessão expirada", session_id=session.session_id)
            return False, None
        
        is_valid = await self.govbr.validate_session(session)
        
        if is_valid:
            session.touch()
            await self.sessions.save(session)
            return True, session
        
        return False, None
    
    async def logout(self, session_id: str | None = None) -> None:
        """
        Encerra uma sessão.
        
        Args:
            session_id: ID da sessão a encerrar.
                       Se None, encerra a mais recente.
        """
        if session_id:
            await self.sessions.delete(session_id)
        else:
            session = await self.sessions.load_latest()
            if session:
                await self.sessions.delete(session.session_id)
        
        logger.info("Sessão encerrada", session_id=session_id)
    
    async def get_session_info(self) -> dict | None:
        """
        Retorna informações da sessão atual.
        
        Returns:
            Dicionário com dados do usuário ou None.
        """
        session = await self.sessions.load_latest()
        
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "cpf": session.cpf,
            "nome": session.nome,
            "is_valid": session.is_valid(),
            "is_govbr_authenticated": session.is_govbr_authenticated,
            "is_sigef_authenticated": session.is_sigef_authenticated,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "last_used_at": session.last_used_at.isoformat() if session.last_used_at else None,
        }
