from unittest import TestCase
from unittest.mock import MagicMock

from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.connection import ConnectionManager
from sqlpinger.core.engine import Engine
from sqlpinger.core.monitor import AvailabilityMonitor


class TestAvailabilityMonitor(TestCase):
    def setUp(self):
        self.server = "localhost"
        self.database = "testdb"
        self.interval = 5
        self.heartbeat_sql = "SENTINEL_HEARTBEAT_SQL"

        # Mock auth strategy and its connection string
        self.auth_strategy = MagicMock(spec=AuthStrategy)
        self.auth_strategy.get_connection_string.return_value = "mock_conn_str"

        # Mock engine: returns a known sentinel SQL and a mock connection manager
        self.connection_manager = MagicMock(spec=ConnectionManager)
        self.engine = MagicMock(spec=Engine)
        self.engine.create_connection_manager.return_value = self.connection_manager
        self.engine.build_heartbeat_sql.return_value = self.heartbeat_sql

        self.monitor = AvailabilityMonitor(
            self.server,
            self.database,
            self.interval,
            self.auth_strategy,
            self.engine,
        )

        # Replace downtime with a mock
        self.monitor.downtime = MagicMock()
        self.monitor.downtime.is_active.return_value = False
        # Mock logger
        self.monitor.logger = MagicMock()

    # --- Contract tests for the engine/auth wiring ---

    def test_init_calls_get_connection_string_once_with_server_and_database(self):
        self.auth_strategy.get_connection_string.assert_called_once_with(self.server, self.database)

    def test_init_creates_connection_manager_via_engine_once(self):
        self.engine.create_connection_manager.assert_called_once_with("mock_conn_str", self.interval)

    def test_run_check_executes_heartbeat_sql_from_engine(self):
        self.engine.build_heartbeat_sql.reset_mock()
        self.connection_manager.execute.reset_mock()

        self.monitor.run_check()

        self.engine.build_heartbeat_sql.assert_called_once_with(self.interval)
        self.connection_manager.execute.assert_called_once_with(self.heartbeat_sql)

    # --- Existing behavior tests ---

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
        self.monitor.downtime.start.assert_not_called()

    def test_handle_exception_when_no_active_downtime_starts_one(self):
        self.monitor.downtime.is_active.return_value = False

        error = Exception("Test error")
        self.monitor.handle_exception(error)

        self.monitor.connection_manager.disconnect.assert_called_once()
        self.monitor.downtime.start.assert_called_once()
        self.monitor.logger.error.assert_called_with(f'❌ Connection failed: {error}')
