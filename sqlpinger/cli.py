import click

import sqlpinger.config as config

from sqlpinger import __version__
from sqlpinger.core.monitor import AvailabilityMonitor
from sqlpinger.credentials_cli import credentials, resolve_sql_auth_credentials
from sqlpinger.engines.postgres import (
    PostgresAuthStrategyFactory,
    PostgresAuthTypes,
    PostgresEngine,
)
from sqlpinger.engines.sqlserver import (
    SqlServerAuthStrategyFactory,
    SqlServerAuthTypes,
    SqlServerEngine,
)


DEFAULT_INTERVAL = 5


def common_options(f):
    f = click.option('--verbose', is_flag=True, help='Enable verbose output')(f)
    f = click.option('--once', is_flag=True, help='Run a single immediate healthcheck and exit')(f)
    f = click.option('--password', required=False, help='Password for SQL authentication')(f)
    f = click.option('--username', required=False, help='Username for SQL authentication')(f)
    f = click.option('--interval', default=DEFAULT_INTERVAL, show_default=True, help='Seconds between each check')(f)
    f = click.option('--database', required=True, help='Database name')(f)
    f = click.option('--server', required=True, help='Database server hostname or IP')(f)
    return f


@click.group()
@click.version_option(__version__)
def cli():
    """Monitor a database continuously and log downtimes."""


cli.add_command(credentials)


def resolve_credentials(
    engine: str,
    auth: str,
    sql_auth: str,
    username: str | None,
    password: str | None,
) -> tuple[str | None, str | None]:
    if auth != sql_auth:
        return username, password
    return resolve_sql_auth_credentials(engine=engine, username=username, password=password)


@cli.command()
@common_options
@click.option('--auth', type=click.Choice(SqlServerAuthTypes.to_list()),
              default=SqlServerAuthTypes.SQL.value, show_default=True)
@click.option('--driver', default='ODBC Driver 18 for SQL Server', show_default=True,
              help='ODBC driver name (SQL Server only)')
def mssql(server, database, interval, auth, username, password, verbose, once, driver):
    """Monitor a SQL Server database."""
    config.verbose = verbose
    effective_interval = DEFAULT_INTERVAL if once else interval
    username, password = resolve_credentials(
        engine='mssql',
        auth=auth,
        sql_auth=SqlServerAuthTypes.SQL.value,
        username=username,
        password=password,
    )
    auth_strategy = SqlServerAuthStrategyFactory.create(
        auth=auth,
        driver=driver,
        timeout_in_seconds=effective_interval,
        username=username,
        password=password,
    )
    monitor = AvailabilityMonitor(server, database, effective_interval, auth_strategy, SqlServerEngine())
    if once:
        if not monitor.run_once():
            click.get_current_context().exit(1)
        return
    monitor.start_monitoring()


@cli.command()
@common_options
@click.option('--auth', type=click.Choice(PostgresAuthTypes.to_list()),
              default=PostgresAuthTypes.SQL.value, show_default=True)
@click.option('--port', type=int, default=5432, show_default=True,
              help='PostgreSQL server port')
@click.option('--sslmode', default='require', show_default=True,
              help='libpq sslmode (disable | allow | prefer | require | verify-ca | verify-full)')
def pg(server, database, interval, auth, username, password, verbose, once, port, sslmode):
    """Monitor a PostgreSQL database."""
    config.verbose = verbose
    effective_interval = DEFAULT_INTERVAL if once else interval
    username, password = resolve_credentials(
        engine='pg',
        auth=auth,
        sql_auth=PostgresAuthTypes.SQL.value,
        username=username,
        password=password,
    )
    auth_strategy = PostgresAuthStrategyFactory.create(
        auth=auth,
        timeout_in_seconds=effective_interval,
        username=username,
        password=password,
        port=port,
        sslmode=sslmode,
    )
    monitor = AvailabilityMonitor(server, database, effective_interval, auth_strategy, PostgresEngine())
    if once:
        if not monitor.run_once():
            click.get_current_context().exit(1)
        return
    monitor.start_monitoring()
