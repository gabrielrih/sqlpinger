from unittest import TestCase

from sqlpinger.engines.postgres.sql_commands import build_pg_sleep_sql


class TestBuildPgSleepSql(TestCase):
    def test_zero_seconds(self):
        self.assertEqual(build_pg_sleep_sql(0), "SELECT pg_sleep(0)")

    def test_small_seconds(self):
        self.assertEqual(build_pg_sleep_sql(5), "SELECT pg_sleep(5)")

    def test_large_seconds(self):
        self.assertEqual(build_pg_sleep_sql(3600), "SELECT pg_sleep(3600)")
