import click

import sqlpinger.config as config

from sqlpinger.core.auth.factory import AuthStrategyFactory
from sqlpinger.core.ping import SqlAvailabilityMonitor


@click.command()
@click.option('--server', required=True, help='SQL Server hostname or IP')
@click.option('--database', required=True, help='Database name')
@click.option('--interval', default=5, show_default=True, help='Seconds between each check')
@click.option('--auth', type=click.Choice(['sql', 'windows', 'azure-ad']), default='azure-ad', show_default=True)
@click.option('--username', help='Username for SQL Server authentication', required = False)
@click.option('--password', help='Password for SQL Server authentication', required = False)
@click.option('--driver', default='ODBC Driver 18 for SQL Server', show_default=True, help='ODBC driver name')
@click.option('--verbose', is_flag = True, help="Enable verbose output")
def main(server, database, interval, auth, username, password, driver, verbose):
    """Ping a SQL Server database continuously and log downtimes"""
    config.verbose = verbose
    auth_strategy = AuthStrategyFactory.create(auth, driver, username, password)
    monitor = SqlAvailabilityMonitor(server, database, interval, auth_strategy)
    monitor.start_monitoring()
