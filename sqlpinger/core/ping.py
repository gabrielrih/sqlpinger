import time

from datetime import datetime

from sqlpinger.core.connection import ConnectionManager
from sqlpinger.core.sql_commands import build_waitfor_delay_sql
from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.downtime import DowntimeSummary
from sqlpinger.util.md5 import calculate_md5
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

        self.downtime_start = None
        self.summary = DowntimeSummary()
        self.last_error_message_hash = None

    def start_monitoring(self):
        self.logger.info(f"Starting monitor for {self.server}/{self.database} every {self.interval}s using {self.auth_strategy.__class__.__name__}")
        try:
            while True:
                try:
                    self.run_check()
                    if self.is_downtime():
                        self.recovery_from_downtime()
                    self.logger.debug('Connection is still healthy')
                except Exception as e:
                    self.handle_exception(e)
                    time.sleep(self.interval)  # wait some time when it fails to avoid retry all the time
        except KeyboardInterrupt:
            self.logger.warning('🛑 Monitoring stopped by user.')
            self.connection_manager.disconnect()
            self.logger.info("📋 Downtime Summary:")
            self.logger.info(str(self.summary))

    def run_check(self):
        sql: str = build_waitfor_delay_sql(seconds = self.interval)
        self.connection_manager.execute(sql)

    def is_downtime(self) -> bool:
        if self.downtime_start:
            return True
        return False

    def recovery_from_downtime(self):
        downtime_end = datetime.now()
        duration = (downtime_end - self.downtime_start).total_seconds()
        self.logger.warning(f"✅ Recovered. Downtime lasted {duration:.2f}s.")
        self.summary.record(self.downtime_start, downtime_end)
        self.downtime_start = None

    def handle_exception(self, error: Exception):
        self.connection_manager.disconnect()
        # when it's the first downtime of the period
        if not self.is_downtime():
            self.downtime_start = datetime.now()
            self.last_error_message_hash = calculate_md5(str(error))
            self.logger.error(f'❌ Connection failed: {error}')
            return  
        self.logger.debug('Connection is still failing!')
