
import click

from sqlpinger.core.auth.factory import AuthStrategyFactory
from sqlpinger.core.ping import SqlAvailabilityMonitor


@click.command()
@click.option('--server', required=True, help='SQL Server hostname or IP')
@click.option('--database', required=True, help='Database name')
@click.option('--interval', default=10, show_default=True, help='Seconds between SELECT 1 pings')
@click.option('--auth', type=click.Choice(['sql', 'azure-ad']), default='azure-ad', show_default=True)
@click.option('--username', help='Username for SQL Server authentication', required = False)
@click.option('--password', help='Password for SQL Server authentication', required = False)
@click.option('--driver', default='ODBC Driver 18 for SQL Server', show_default=True, help='ODBC driver name')
def main(server, database, interval, auth, username, password, driver):
    """Ping a SQL Server database continuously and log downtimes"""
    auth_strategy = AuthStrategyFactory.create(auth, driver, username, password)

    monitor = SqlAvailabilityMonitor(server, database, interval, auth_strategy)
    monitor.start_monitoring()
