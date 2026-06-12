import click

from sqlpinger.core.credentials import (
    CredentialStoreError,
    DefaultCredentialStore,
    SUPPORTED_CREDENTIAL_ENGINES,
)
from sqlpinger.util.logger import Logger


def resolve_sql_auth_credentials(
    engine: str,
    username: str | None,
    password: str | None,
) -> tuple[str | None, str | None]:
    if password and not username:
        raise click.ClickException(
            "The --password option requires --username. "
            "Omit both options to use default credentials for SQL authentication."
        )

    if username:
        if not password:
            password = click.prompt(f'Password for user "{username}"', hide_input=True, type=str)
        return username, password

    try:
        default_credentials = DefaultCredentialStore().get_default(engine)
    except CredentialStoreError as exc:
        raise click.ClickException(str(exc)) from exc

    if default_credentials is None:
        raise click.ClickException(
            "SQL authentication requires --username/--password or default credentials. "
            f"Configure defaults with: sqlpinger credentials set --engine {engine} --username <user>"
        )

    Logger.get_logger(__name__).info(
        f'Using saved default credentials for {engine} with user "{default_credentials.username}".'
    )
    return default_credentials.username, default_credentials.password


@click.group()
def credentials():
    """Manage default SQL credentials."""


@credentials.command(name='set')
@click.option('--engine', type=click.Choice(SUPPORTED_CREDENTIAL_ENGINES), required=True,
              help='Engine that will use these default credentials')
@click.option('--username', required=True, help='Default username for SQL authentication')
def set_credentials(engine, username):
    """Save default SQL credentials for an engine."""
    password = click.prompt(f'Default password for "{username}"', hide_input=True, type=str)
    try:
        DefaultCredentialStore().set_default(engine, username, password)
    except CredentialStoreError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f'Default credentials configured for {engine} user "{username}".')


@credentials.command(name='status')
@click.option('--engine', type=click.Choice(SUPPORTED_CREDENTIAL_ENGINES), required=False,
              help='Show only one engine')
def status_credentials(engine):
    """Show default credential status without revealing passwords."""
    engines = (engine,) if engine else SUPPORTED_CREDENTIAL_ENGINES
    store = DefaultCredentialStore()
    for current_engine in engines:
        try:
            default_credentials = store.get_default(current_engine)
        except CredentialStoreError as exc:
            raise click.ClickException(str(exc)) from exc

        if default_credentials:
            click.echo(f'{current_engine}: configured for user "{default_credentials.username}"')
        else:
            click.echo(f'{current_engine}: not configured')


@credentials.command(name='clear')
@click.option('--engine', type=click.Choice(SUPPORTED_CREDENTIAL_ENGINES), required=True,
              help='Engine whose default credentials will be removed')
def clear_credentials(engine):
    """Remove default SQL credentials for an engine."""
    try:
        removed = DefaultCredentialStore().clear_default(engine)
    except CredentialStoreError as exc:
        raise click.ClickException(str(exc)) from exc

    if removed:
        click.echo(f'Default credentials cleared for {engine}.')
    else:
        click.echo(f'No default credentials configured for {engine}.')
