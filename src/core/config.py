"""
Gov-Auth Enterprise API
Configurações por ambiente
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Base path calculado uma vez
_BASE_PATH = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Configurações da aplicação com validação via Pydantic."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "Gov-Auth API"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    
    # API
    api_prefix: str = "/api/v1"
    api_key: str = "dev-api-key-change-in-production"
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 4
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    access_token_expire_minutes: int = 60
    
    # Gov.br
    govbr_login_url: str = "https://sso.acesso.gov.br"
    govbr_session_timeout_hours: int = 4
    
    # SIGEF
    sigef_base_url: str = "https://sigef.incra.gov.br"
    sigef_session_timeout_hours: int = 4
    
    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"
    
    # Browser
    browser_headless: bool = False
    browser_timeout_ms: int = 30000
    
    @property
    def base_path(self) -> Path:
        """Caminho base do projeto."""
        return _BASE_PATH
    
    @property
    def data_path(self) -> Path:
        """Diretório de dados."""
        return self.base_path / "data"
    
    @property
    def sessions_path(self) -> Path:
        """Diretório de sessões."""
        return self.data_path / "sessions"
    
    @property
    def downloads_path(self) -> Path:
        """Diretório de downloads."""
        return self.data_path / "downloads"
    
    @property
    def logs_path(self) -> Path:
        """Diretório de logs."""
        return self.base_path / "logs"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    # Aliases para compatibilidade
    @property
    def data_dir(self) -> Path:
        return self.data_path
    
    @property
    def sessions_dir(self) -> Path:
        return self.sessions_path
    
    @property
    def downloads_dir(self) -> Path:
        return self.downloads_path
    
    @property
    def logs_dir(self) -> Path:
        return self.logs_path
    
    @property
    def cors_origins(self) -> list[str]:
        """Retorna lista de origens CORS."""
        # Em produção, seria configurável via env var
        if self.is_production:
            return []
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
