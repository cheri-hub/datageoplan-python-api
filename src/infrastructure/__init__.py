"""
Camada de infraestrutura.

Contém implementações concretas das interfaces do domínio:
- Integrações externas (Gov.br, SIGEF)
- Persistência (repositórios)
- Clientes HTTP
"""

from src.infrastructure.govbr import PlaywrightGovBrAuthenticator
from src.infrastructure.persistence import FileSessionRepository, create_new_session
from src.infrastructure.sigef import HttpSigefClient

__all__ = [
    "PlaywrightGovBrAuthenticator",
    "HttpSigefClient",
    "FileSessionRepository",
    "create_new_session",
]
