"""
CLI para Gov.br Auth API.

Permite executar operações via linha de comando.
"""

import asyncio
import sys
from pathlib import Path

import click

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.infrastructure.govbr import PlaywrightGovBrAuthenticator
from src.infrastructure.sigef import HttpSigefClient
from src.infrastructure.persistence import FileSessionRepository
from src.services.auth_service import AuthService
from src.services.sigef_service import SigefService


def get_services():
    """Inicializa serviços."""
    setup_logging()
    
    session_repo = FileSessionRepository()
    govbr_auth = PlaywrightGovBrAuthenticator()
    sigef_client = HttpSigefClient()
    
    auth_service = AuthService(
        govbr_authenticator=govbr_auth,
        sigef_client=sigef_client,
        session_repository=session_repo,
    )
    
    sigef_service = SigefService(
        sigef_client=sigef_client,
        session_repository=session_repo,
        auth_service=auth_service,
    )
    
    return auth_service, sigef_service


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Gov.br Auth CLI - Autenticação e download SIGEF."""
    pass


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Força nova autenticação")
def login(force: bool):
    """Realiza login no Gov.br."""
    
    async def _login():
        auth_service, _ = get_services()
        
        click.echo("🔐 Iniciando autenticação Gov.br...")
        click.echo("📋 Por favor, selecione o certificado digital no navegador.")
        
        session = await auth_service.get_or_create_session(force_new=force)
        
        click.echo(f"\n✅ Login realizado com sucesso!")
        click.echo(f"   👤 Nome: {session.nome}")
        click.echo(f"   📄 CPF: {session.cpf}")
        click.echo(f"   🆔 Session ID: {session.session_id}")
    
    asyncio.run(_login())


@cli.command()
def status():
    """Verifica status da sessão atual."""
    
    async def _status():
        auth_service, _ = get_services()
        
        is_valid, session = await auth_service.validate_current_session()
        
        if is_valid and session:
            click.echo("✅ Sessão válida")
            click.echo(f"   👤 Nome: {session.nome}")
            click.echo(f"   📄 CPF: {session.cpf}")
            click.echo(f"   🕐 Criada: {session.created_at}")
            click.echo(f"   ⏰ Expira: {session.expires_at}")
            click.echo(f"   🏛️ Gov.br: {'✓' if session.is_govbr_authenticated else '✗'}")
            click.echo(f"   📍 SIGEF: {'✓' if session.is_sigef_authenticated else '✗'}")
        else:
            click.echo("❌ Nenhuma sessão válida encontrada")
            click.echo("   Use 'gov-auth login' para autenticar")
    
    asyncio.run(_status())


@cli.command()
def logout():
    """Encerra a sessão atual."""
    
    async def _logout():
        auth_service, _ = get_services()
        await auth_service.logout()
        click.echo("✅ Logout realizado com sucesso")
    
    asyncio.run(_logout())


@cli.command()
@click.argument("codigo")
@click.option(
    "--tipo", "-t",
    type=click.Choice(["parcela", "vertice", "limite", "all"]),
    default="all",
    help="Tipo de exportação",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Diretório de saída",
)
def download(codigo: str, tipo: str, output: str | None):
    """Baixa CSVs de uma parcela SIGEF."""
    
    async def _download():
        _, sigef_service = get_services()
        
        output_dir = Path(output) if output else None
        
        click.echo(f"📥 Baixando dados da parcela: {codigo}")
        
        if tipo == "all":
            results = await sigef_service.download_all_csvs(
                codigo=codigo,
                destino_dir=output_dir,
            )
            
            click.echo("\n✅ Downloads concluídos:")
            for tipo_csv, path in results.items():
                click.echo(f"   📄 {tipo_csv}: {path}")
        else:
            path = await sigef_service.download_csv(
                codigo=codigo,
                tipo=tipo,
                destino=output_dir / f"{codigo}_{tipo}.csv" if output_dir else None,
            )
            click.echo(f"\n✅ Download concluído: {path}")
    
    asyncio.run(_download())


@cli.command()
@click.argument("codigos", nargs=-1, required=True)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Diretório de saída",
)
def batch(codigos: tuple[str, ...], output: str | None):
    """Baixa CSVs de múltiplas parcelas."""
    
    async def _batch():
        _, sigef_service = get_services()
        
        output_dir = Path(output) if output else None
        
        click.echo(f"📥 Baixando dados de {len(codigos)} parcelas...")
        
        results = await sigef_service.download_batch(
            codigos=list(codigos),
            destino_dir=output_dir,
        )
        
        success = sum(1 for r in results.values() if "error" not in r)
        failures = sum(1 for r in results.values() if "error" in r)
        
        click.echo(f"\n📊 Resultado: {success} sucesso, {failures} falhas")
        
        for codigo, arquivos in results.items():
            if "error" in arquivos:
                click.echo(f"   ❌ {codigo}: {arquivos['error']}")
            else:
                click.echo(f"   ✅ {codigo}: {len(arquivos)} arquivos")
    
    asyncio.run(_batch())


@cli.command()
def serve():
    """Inicia servidor da API."""
    import uvicorn
    
    settings = get_settings()
    
    click.echo(f"🚀 Iniciando servidor em http://{settings.host}:{settings.port}")
    click.echo("   📖 Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    cli()
