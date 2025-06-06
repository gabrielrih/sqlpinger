from unittest import TestCase
from unittest.mock import MagicMock, patch

from sqlpinger.core.ping import SqlAvailabilityMonitor
from sqlpinger.core.downtime import DowntimeSummary
from sqlpinger.core.auth.base import AuthStrategy



class TestSqlAvailabilityMonitor(TestCase):
    def setUp(self):
        self.server = "localhost"
        self.database = "testdb"
        self.interval = 5

        # Mock auth strategy and its connection string
        self.auth_strategy = MagicMock(spec=AuthStrategy)
        self.auth_strategy.get_connection_string.return_value = "mock_conn_str"

        self.monitor = SqlAvailabilityMonitor(
            self.server,
            self.database,
            self.interval,
            self.auth_strategy
        )

        # Replace connection manager with a mock
        self.monitor.connection_manager = MagicMock()
        # Replace downtime with a mock
        self.monitor.downtime = MagicMock()
        self.monitor.downtime.is_active.return_value = False
        # Mock logger
        self.monitor.logger = MagicMock()

    def test_run_check_executes_sql(self):
        self.monitor.run_check()
        self.monitor.connection_manager.execute.assert_called_once()

    def test_recover_from_downtime_logs_duration(self):
        self.monitor.downtime.finish.return_value = 42

        self.monitor.recover_from_downtime()

        self.monitor.logger.warning.assert_called_with("✅ Recovered. Downtime lasted 42s.")

    def test_handle_exception_when_downtime_already_active(self):
        self.monitor.downtime.is_active.return_value = True

        error = Exception("Test error")
        self.monitor.handle_exception(error)

        self.monitor.connection_manager.disconnect.assert_called_once()
        self.monitor.logger.debug.assert_called_with(f'❌ Connection is still failing: {error}')
        self.monitor.logger.error.assert_not_called()
        self.monitor.downtime
