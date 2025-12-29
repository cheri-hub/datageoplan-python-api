"""
Interfaces (contratos) do domínio.

Seguindo o princípio de Inversão de Dependência (DIP do SOLID),
definimos abstrações que serão implementadas pela camada de infraestrutura.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from src.domain.entities import Parcela, Session, TipoExportacao


class ISessionRepository(ABC):
    """
    Interface para persistência de sessões.
    
    Permite diferentes implementações:
    - FileSessionRepository (JSON em disco)
    - RedisSessionRepository (cache distribuído)
    - DatabaseSessionRepository (PostgreSQL, etc.)
    """
    
    @abstractmethod
    async def save(self, session: Session) -> None:
        """Persiste uma sessão."""
        ...
    
    @abstractmethod
    async def load(self, session_id: str) -> Session | None:
        """Carrega uma sessão pelo ID."""
        ...
    
    @abstractmethod
    async def load_latest(self) -> Session | None:
        """Carrega a sessão mais recente."""
        ...
    
    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Remove uma sessão."""
        ...
    
    @abstractmethod
    async def list_all(self) -> list[Session]:
        """Lista todas as sessões."""
        ...


class IGovBrAuthenticator(ABC):
    """
    Interface para autenticação no Gov.br.
    
    Abstrai a complexidade do Playwright e permite
    diferentes estratégias de autenticação.
    """
    
    @abstractmethod
    async def authenticate(self, headless: bool = False) -> Session:
        """
        Realiza autenticação interativa no Gov.br.
        
        Args:
            headless: Se True, tenta autenticação sem interface.
                      Requer sessão prévia válida.
        
        Returns:
            Session com tokens e cookies do Gov.br.
        """
        ...
    
    @abstractmethod
    async def validate_session(self, session: Session) -> bool:
        """
        Valida se uma sessão ainda está ativa.
        
        Args:
            session: Sessão a ser validada.
        
        Returns:
            True se a sessão é válida e pode ser usada.
        """
        ...
    
    @abstractmethod
    async def refresh_session(self, session: Session) -> Session:
        """
        Tenta renovar uma sessão existente.
        
        Args:
            session: Sessão a ser renovada.
        
        Returns:
            Nova sessão com tokens atualizados.
        """
        ...


class ISigefClient(ABC):
    """
    Interface para operações no SIGEF INCRA.
    
    Permite tanto implementação via browser (Playwright)
    quanto via requisições HTTP diretas.
    """
    
    @abstractmethod
    async def authenticate(self, govbr_session: Session) -> Session:
        """
        Autentica no SIGEF usando sessão do Gov.br.
        
        Args:
            govbr_session: Sessão autenticada do Gov.br.
        
        Returns:
            Session com cookies do SIGEF adicionados.
        """
        ...
    
    @abstractmethod
    async def get_parcela(self, codigo: str, session: Session) -> Parcela:
        """
        Obtém dados de uma parcela.
        
        Args:
            codigo: Código SIGEF da parcela.
            session: Sessão autenticada no SIGEF.
        
        Returns:
            Dados da parcela.
        """
        ...
    
    @abstractmethod
    async def download_csv(
        self,
        codigo: str,
        tipo: TipoExportacao,
        session: Session,
        destino: Path | None = None,
    ) -> Path:
        """
        Baixa CSV de uma parcela.
        
        Args:
            codigo: Código SIGEF da parcela.
            tipo: Tipo de exportação (parcela, vertice, limite).
            session: Sessão autenticada no SIGEF.
            destino: Caminho de destino. Se None, usa padrão.
        
        Returns:
            Caminho do arquivo baixado.
        """
        ...
    
    @abstractmethod
    async def download_all_csvs(
        self,
        codigo: str,
        session: Session,
        destino_dir: Path | None = None,
    ) -> dict[TipoExportacao, Path]:
        """
        Baixa todos os CSVs de uma parcela.
        
        Args:
            codigo: Código SIGEF da parcela.
            session: Sessão autenticada no SIGEF.
            destino_dir: Diretório de destino.
        
        Returns:
            Dicionário com tipo -> caminho do arquivo.
        """
        ...
    
    @abstractmethod
    async def download_memorial(
        self,
        codigo: str,
        session: Session,
        destino: Path | None = None,
    ) -> Path:
        """
        Baixa memorial descritivo (PDF) de uma parcela.
        
        Args:
            codigo: Código SIGEF da parcela.
            session: Sessão autenticada no SIGEF.
            destino: Caminho de destino. Se None, usa padrão.
        
        Returns:
            Caminho do arquivo PDF baixado.
        """
        ...


class INotificationService(Protocol):
    """
    Protocol para serviço de notificações.
    
    Usando Protocol permite duck typing - qualquer classe
    que implemente estes métodos é válida.
    """
    
    def notify_auth_required(self, message: str) -> None:
        """Notifica que autenticação é necessária."""
        ...
    
    def notify_download_complete(self, files: list[Path]) -> None:
        """Notifica que downloads foram concluídos."""
        ...
    
    def notify_error(self, error: Exception) -> None:
        """Notifica erro."""
        ...
