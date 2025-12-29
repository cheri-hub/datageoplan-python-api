"""
Configuração de testes pytest.
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.v1.dependencies import reset_dependencies
from src.core.config import get_settings
from src.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Cria event loop para testes async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """Cliente de teste síncrono."""
    # Reset dependências para cada teste
    reset_dependencies()
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Cliente de teste assíncrono."""
    reset_dependencies()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> Path:
    """Diretório temporário para dados de teste."""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    """Configura ambiente de teste."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # Limpa cache de settings
    get_settings.cache_clear()
    
    # Limpa sessões de teste existentes
    settings = get_settings()
    sessions_dir = settings.sessions_dir
    if sessions_dir.exists():
        for f in sessions_dir.glob("session_*.json"):
            f.unlink()
