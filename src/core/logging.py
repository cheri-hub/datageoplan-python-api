"""
Configuração de logging estruturado.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from src.core.config import get_settings


def setup_logging() -> None:
    """Configura logging estruturado para a aplicação."""
    settings = get_settings()
    
    # Processadores compartilhados
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]
    
    if settings.log_format == "json":
        # Produção: JSON estruturado
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Desenvolvimento: Console colorido
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configura handler do stdlib
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    )
    
    # Configura root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)
    
    # Reduz verbosidade de bibliotecas externas
    for logger_name in ["httpx", "httpcore", "playwright", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Retorna logger configurado para o módulo."""
    return structlog.get_logger(name)
