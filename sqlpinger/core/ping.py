import time

from sqlpinger.core.connection import ConnectionManager
from sqlpinger.core.sql_commands import build_waitfor_delay_sql
from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.downtime import Downtime, DowntimeSummary
from sqlpinger.util.logger import Logger


class SqlAvailabilityMonitor:
    def __init__(self, server: str, database: str, interval: int, auth_strategy: AuthStrategy):
        self.server = server
        self.database = database
        self.interval = interval
        self.auth_strategy = auth_strategy
        self.logger = Logger.get_logger(__name__)
        conn_str = auth_strategy.get_connection_string(server, database)
        self.connection_manager = ConnectionManager(conn_str, timeout = interval)
        self.summary = DowntimeSummary()
        self.downtime = Downtime(summary = self.summary)

    def start_monitoring(self):
        self.logger.info(f"Starting monitor for {self.server}/{self.database} every {self.interval}s using {self.auth_strategy.__class__.__name__}")
        try:
            while True:
                try:
                    self.run_check()
                    if self.downtime.is_active():
                        self.recover_from_downtime()
                    self.logger.debug('Connection is still healthy')
                except Exception as e:
                    self.handle_exception(e)
                    time.sleep(self.interval)  # wait some time when it fails to avoid retry all the time
        except KeyboardInterrupt:
            self.logger.warning('🛑 Monitoring stopped by user.')
            self.connection_manager.disconnect()
            self.logger.info("📋 Downtime Summary:")
            self.logger.info(self.summary)

    def run_check(self):
        sql: str = build_waitfor_delay_sql(seconds = self.interval)
        self.connection_manager.execute(sql)

    def recover_from_downtime(self):
        duration: int = self.downtime.finish()
        self.logger.warning(f"✅ Recovered. Downtime lasted {duration}s.")

    def handle_exception(self, error: Exception):
        self.connection_manager.disconnect()
        if self.downtime.is_active():
            self.logger.debug(f'❌ Connection is still failing: {error}')
            return
        self.downtime.start()
        self.logger.error(f'❌ Connection failed: {error}')
