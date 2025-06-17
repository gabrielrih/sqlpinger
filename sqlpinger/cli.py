import click

import sqlpinger.config as config

from sqlpinger import __version__
from sqlpinger.core.auth.common import AuthStrategyFactory, AuthTypes
from sqlpinger.core.ping import SqlAvailabilityMonitor


@click.command()
@click.option('--server', required=True, help='SQL Server hostname or IP')
@click.option('--database', required=True, help='Database name')
@click.option('--interval', default=5, show_default=True, help='Seconds between each check')
@click.option('--auth', type=click.Choice(AuthTypes.to_list()), default=AuthTypes.AZURE_AD.value, show_default=True)
@click.option('--username', help='Username for SQL Server authentication', required = False)
@click.option('--password', help='Password for SQL Server authentication', required = False)
@click.option('--driver', default='ODBC Driver 18 for SQL Server', show_default=True, help='ODBC driver name')
@click.option('--verbose', is_flag = True, help="Enable verbose output")
@click.version_option(__version__)
def main(server, database, interval, auth, username, password, driver, verbose):
    """Monitor a SQL Server database continuously and log downtimes"""
    config.verbose = verbose
    if auth == AuthTypes.SQL.value and not password:
        password = click.prompt(f'Password for user "{username}"', hide_input = True, type = str)
    auth_strategy = AuthStrategyFactory.create(
        auth = auth,
        driver = driver,
        timeout_in_seconds = interval,
        username = username,
        password = password
    )
    monitor = SqlAvailabilityMonitor(server, database, interval, auth_strategy)
    monitor.start_monitoring()

