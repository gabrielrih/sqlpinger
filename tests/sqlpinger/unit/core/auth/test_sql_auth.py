from unittest import TestCase

from sqlpinger.core.auth.sql_auth import SqlAuth


class TestSqlAuth(TestCase):
    def setUp(self):
        self.driver = 'any'
        self.server = 'server.database.windows.net'
        self.database = 'database'
        self.username = 'username'
        self.password = 'password'

    def test_get_connection_string(self):
        # Given
        expected_conn_string: str = f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};'

        # When
        auth = SqlAuth(username = self.username, password = self.password, driver = self.driver)
        conn_string = auth.get_connection_string(self.server, self.database)

        # Then
        self.assertEqual(conn_string, expected_conn_string)
