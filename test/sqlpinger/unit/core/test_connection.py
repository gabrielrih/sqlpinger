from unittest import TestCase
from unittest.mock import patch, MagicMock

from sqlpinger.core.connection import ConnectionManager



class TestConnectionManager(TestCase):
    def setUp(self):
        self.conn_str = "DRIVER={ODBC Driver};SERVER=localhost;DATABASE=testdb"
        self.timeout = 5
        self.manager = ConnectionManager(self.conn_str, self.timeout)

    @patch("sqlpinger.core.connection.pyodbc.connect")
    def test_connect(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        self.manager.connect()

        mock_connect.assert_called_once_with(self.conn_str, timeout=self.timeout)
        self.assertEqual(self.manager.conn, mock_conn)

    def test_is_connected_true(self):
        mock_conn = MagicMock()
        mock_conn.closed = False
        self.manager.conn = mock_conn

        self.assertTrue(self.manager.is_connected())

    def test_is_connected_false_when_none(self):
        self.manager.conn = None
        self.assertFalse(self.manager.is_connected())

    def test_is_connected_false_when_closed(self):
        mock_conn = MagicMock()
        mock_conn.closed = True
        self.manager.conn = mock_conn

        self.assertFalse(self.manager.is_connected())

    @patch("sqlpinger.core.connection.pyodbc.connect")
    def test_execute_calls_connect_and_executes_sql(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        self.manager.conn = None  # simulate disconnected
        self.manager.execute("SELECT 1")

        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT 1")

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
