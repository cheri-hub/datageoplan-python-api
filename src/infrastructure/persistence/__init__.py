"""
Módulo de persistência.
"""

from src.infrastructure.persistence.session_repository import (
    FileSessionRepository,
    create_new_session,
)

__all__ = [
    "FileSessionRepository",
    "create_new_session",
]
