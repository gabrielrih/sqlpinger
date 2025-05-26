from unittest import TestCase

from sqlpinger.core.auth.azure_ad import AzureADInteractive


class TestAzureADInteractive(TestCase):
    def setUp(self):
        self.driver = 'any'
        self.server = 'server.database.windows.net'
        self.database = 'database'

    def test_get_connection_string(self):
        # Given
        expected_conn_string: str = f'DRIVER={{{self.driver}}};SERVER={self.server};DATABASE={self.database};Authentication=ActiveDirectoryInteractive;'

        # When
        auth = AzureADInteractive(driver = self.driver)
        conn_string = auth.get_connection_string(self.server, self.database)

        # Then
        self.assertEqual(conn_string, expected_conn_string)
