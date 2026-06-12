from unittest import TestCase
from unittest.mock import patch, MagicMock

from sqlpinger.engines.postgres.connection import PostgresConnectionManager


class TestPostgresConnectionManager(TestCase):
    def setUp(self):
        self.conn_str = "postgresql://u:p@host:5432/db?connect_timeout=5&sslmode=require"
        self.timeout = 5
        self.manager = PostgresConnectionManager(self.conn_str, self.timeout)

    @patch("sqlpinger.engines.postgres.connection.psycopg2.connect")
    def test_connect_passes_connect_timeout(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        self.manager.connect()

        mock_connect.assert_called_once_with(self.conn_str, connect_timeout=self.timeout)
        self.assertEqual(self.manager.conn, mock_conn)

    def test_is_connected_true_when_closed_zero(self):
        mock_conn = MagicMock()
        mock_conn.closed = 0
        self.manager.conn = mock_conn

        self.assertTrue(self.manager.is_connected())

    def test_is_connected_false_when_none(self):
        self.manager.conn = None
        self.assertFalse(self.manager.is_connected())

    def test_is_connected_false_when_closed_nonzero(self):
        mock_conn = MagicMock()
        mock_conn.closed = 1
        self.manager.conn = mock_conn

        self.assertFalse(self.manager.is_connected())

    @patch("sqlpinger.engines.postgres.connection.psycopg2.connect")
    def test_execute_calls_connect_and_executes_sql(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.closed = 0
        mock_connect.return_value = mock_conn

        self.manager.conn = None  # simulate disconnected
        self.manager.execute("SELECT pg_sleep(1)")

        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT pg_sleep(1)")
        mock_cursor.close.assert_called_once_with()

    def test_disconnect_closes_connection(self):
        mock_conn = MagicMock()
        self.manager.conn = mock_conn

        self.manager.disconnect()

        mock_conn.close.assert_called_once()
        self.assertIsNone(self.manager.conn)

    def test_disconnect_handles_exception_safely(self):
        mock_conn = MagicMock()
        mock_conn.close.side_effect = Exception("fail")
        self.manager.conn = mock_conn

        # Should not raise
        self.manager.disconnect()

        self.assertIsNone(self.manager.conn)
