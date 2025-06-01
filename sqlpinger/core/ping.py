import time
import pyodbc

from datetime import datetime

from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.summary import DowntimeSummary
from sqlpinger.util.md5 import calculate_md5
from sqlpinger.util.logger import Logger


class SqlAvailabilityMonitor:
    def __init__(self, server: str, database: str, interval: int, auth_strategy: AuthStrategy):
        self.server = server
        self.database = database
        self.interval = interval
        self.auth_strategy = auth_strategy

        self.logger = Logger.get_logger(__name__)
        self.conn_str = auth_strategy.get_connection_string(server, database)
        self.conn = None
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
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.logger.warning('🛑 Monitoring stopped by user.')
            self.disconnect()
            self.logger.info("📋 Downtime Summary:")
            self.logger.info(str(self.summary))

    def run_check(self):
        if self.conn is None or self.conn.closed:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchall()

    def connect(self):
        self.conn = pyodbc.connect(self.conn_str, timeout=self.interval)
        self.logger.info("✅ Connection is healthy")

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
        self.disconnect()
        # when it's the first downtime of the period
        if not self.is_downtime():
            self.downtime_start = datetime.now()
            self.last_error_message_hash = calculate_md5(str(error))
            self.logger.error(f'❌ Connection failed: {error}')
            return  
        self.logger.debug('❌ Connection is still failing!')

    def disconnect(self):
        if not self.conn:
            return
        try:
            self.conn.close()
        except:
            pass
        self.conn = None
