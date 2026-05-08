from unittest import TestCase

from sqlpinger.engines.postgres.auth.sql_auth import PostgresSqlAuth


class TestPostgresSqlAuth(TestCase):
    def test_trivial_credentials(self):
        auth = PostgresSqlAuth(
            username="u",
            password="p",
            port=5432,
            sslmode="require",
            timeout_in_seconds=5,
        )
        conn_str = auth.get_connection_string("host", "db")
        self.assertEqual(
            conn_str,
            "postgresql://u:p@host:5432/db?connect_timeout=5&sslmode=require",
        )

    def test_special_chars_in_password_are_percent_encoded(self):
        auth = PostgresSqlAuth(
            username="user@tenant",
            password="p@ss word!",
            port=5432,
            sslmode="require",
            timeout_in_seconds=5,
        )
        conn_str = auth.get_connection_string("host", "db")
        self.assertEqual(
            conn_str,
            "postgresql://user%40tenant:p%40ss%20word%21@host:5432/db"
            "?connect_timeout=5&sslmode=require",
        )

    def test_password_with_quote_and_backslash_is_percent_encoded(self):
        auth = PostgresSqlAuth(
            username="u",
            password="pa'ss\\x",
            port=5432,
            sslmode="require",
            timeout_in_seconds=5,
        )
        conn_str = auth.get_connection_string("host", "db")
        self.assertIn("pa%27ss%5Cx", conn_str)
        self.assertNotIn("'", conn_str)
        self.assertNotIn("\\", conn_str)

    def test_non_default_port_and_sslmode_flow_through(self):
        auth = PostgresSqlAuth(
            username="u",
            password="p",
            port=6543,
            sslmode="verify-full",
            timeout_in_seconds=10,
        )
        conn_str = auth.get_connection_string("host", "db")
        self.assertEqual(
            conn_str,
            "postgresql://u:p@host:6543/db?connect_timeout=10&sslmode=verify-full",
        )
