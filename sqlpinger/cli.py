import click

import sqlpinger.config as config

from sqlpinger import __version__
from sqlpinger.core.monitor import AvailabilityMonitor
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


def common_options(f):
    f = click.option('--verbose', is_flag=True, help='Enable verbose output')(f)
    f = click.option('--password', required=False, help='Password for SQL authentication')(f)
    f = click.option('--username', required=False, help='Username for SQL authentication')(f)
    f = click.option('--interval', default=5, show_default=True, help='Seconds between each check')(f)
    f = click.option('--database', required=True, help='Database name')(f)
    f = click.option('--server', required=True, help='Database server hostname or IP')(f)
    return f


@click.group()
@click.version_option(__version__)
def cli():
    """Monitor a database continuously and log downtimes."""


@cli.command()
@common_options
@click.option('--auth', type=click.Choice(SqlServerAuthTypes.to_list()),
              default=SqlServerAuthTypes.SQL.value, show_default=True)
@click.option('--driver', default='ODBC Driver 18 for SQL Server', show_default=True,
              help='ODBC driver name (SQL Server only)')
def mssql(server, database, interval, auth, username, password, verbose, driver):
    """Monitor a SQL Server database."""
    config.verbose = verbose
    if auth == SqlServerAuthTypes.SQL.value and not password:
        password = click.prompt(f'Password for user "{username}"', hide_input=True, type=str)
    auth_strategy = SqlServerAuthStrategyFactory.create(
        auth=auth,
        driver=driver,
        timeout_in_seconds=interval,
        username=username,
        password=password,
    )
    monitor = AvailabilityMonitor(server, database, interval, auth_strategy, SqlServerEngine())
    monitor.start_monitoring()


@cli.command()
@common_options
@click.option('--auth', type=click.Choice(PostgresAuthTypes.to_list()),
              default=PostgresAuthTypes.SQL.value, show_default=True)
@click.option('--port', type=int, default=5432, show_default=True,
              help='PostgreSQL server port')
@click.option('--sslmode', default='require', show_default=True,
              help='libpq sslmode (disable | allow | prefer | require | verify-ca | verify-full)')
def pg(server, database, interval, auth, username, password, verbose, port, sslmode):
    """Monitor a PostgreSQL database."""
    config.verbose = verbose
    if auth == PostgresAuthTypes.SQL.value and not password:
        password = click.prompt(f'Password for user "{username}"', hide_input=True, type=str)
    auth_strategy = PostgresAuthStrategyFactory.create(
        auth=auth,
        timeout_in_seconds=interval,
        username=username,
        password=password,
        port=port,
        sslmode=sslmode,
    )
    monitor = AvailabilityMonitor(server, database, interval, auth_strategy, PostgresEngine())
    monitor.start_monitoring()
