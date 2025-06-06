from unittest import TestCase

from sqlpinger.core.auth.windows_auth import WindowsAuth


class TestWindowsAuth(TestCase):
    def setUp(self):
        self.driver = 'any'
        self.server = 'server.database.windows.net'
        self.database = 'database'
        self.timeout_in_seconds = 10

    def test_get_connection_string(self):
        # Given
        expected_conn_string: str = f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;TrustServerCertificate=yes;Connection Timeout={self.timeout_in_seconds};'

        # When
        auth = WindowsAuth(driver = self.driver, timeout_in_seconds = self.timeout_in_seconds)
        conn_string = auth.get_connection_string(self.server, self.database)

        # Then
        self.assertEqual(conn_string, expected_conn_string)
