from unittest import TestCase

from sqlpinger.core.sql_commands import build_waitfor_delay_sql


class TestStandaloneMethods(TestCase):
    def test_build_waitfor_delay_sql_when_seconds(self):
        seconds: int = 10
        expected_sql = "WAITFOR DELAY '00:00:10'"
        sql = build_waitfor_delay_sql(seconds = seconds)
        self.assertEqual(expected_sql, sql)

    def test_build_waitfor_delay_sql_when_minutes(self):
        seconds: int = 90
        expected_sql = "WAITFOR DELAY '00:01:30'"
        sql = build_waitfor_delay_sql(seconds = seconds)
        self.assertEqual(expected_sql, sql)
    def test_build_waitfor_delay_sql_when_hours(self):
        seconds: int = 3610
        expected_sql = "WAITFOR DELAY '01:00:10'"
        sql = build_waitfor_delay_sql(seconds = seconds)
        self.assertEqual(expected_sql, sql)
