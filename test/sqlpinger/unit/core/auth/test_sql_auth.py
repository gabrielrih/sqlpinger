from unittest import TestCase

from sqlpinger.core.auth.sql_auth import SqlAuth


class TestSqlAuth(TestCase):
    def setUp(self):
        self.driver = 'any'
        self.server = 'server.database.windows.net'
        self.database = 'database'
        self.username = 'username'
        self.password = 'password'
        self.timeout_in_seconds = 10

    def test_get_connection_string(self):
        # Given
        expected_conn_string: str = f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};Connection Timeout={self.timeout_in_seconds};TrustServerCertificate=yes;'

        # When
        auth = SqlAuth(username = self.username, password = self.password, driver = self.driver, timeout_in_seconds = self.timeout_in_seconds)
        conn_string = auth.get_connection_string(self.server, self.database)

        # Then
        self.assertEqual(conn_string, expected_conn_string)
