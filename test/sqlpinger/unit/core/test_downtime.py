import time

from unittest import TestCase
from freezegun import freeze_time
from datetime import datetime, timedelta
from typing import Dict
from datetime import datetime

from sqlpinger.core.downtime import DowntimeSummary, Downtime


class TestDowntimeSummary(TestCase):
    def test_record(self):
        summary = DowntimeSummary()
        self.assertEqual(len(summary.downtimes), 0)
        summary.record(
            start = datetime.now(),
            end = datetime.now()
        )
        self.assertEqual(len(summary.downtimes), 1)

    @freeze_time("2025-05-26 10:00:00")  # mocking datetime.now()
    def test_to_dict(self):
        # Given
        expected_response: Dict = {
            "summary": {
                "downtimes_quantity": 1,
                "total_downtime": "600 seconds"
            },
            "downtimes": [
                {
                    "from": "2025-05-26 09:50:00",
                    "to": "2025-05-26 10:00:00",
                    "time": "600 seconds"
                }
            ]
        }
        now = datetime.now()  # mocked

        # When
        summary = DowntimeSummary()
        summary.record(
            start = now - timedelta(minutes = 10),
            end = now
        )
        response: Dict = summary.to_dict()

        # Then
        self.assertEqual(response, expected_response)

    def test_printing_it(self):
        summary = DowntimeSummary()
        self.assertIsNotNone(str(summary))


class TestDowntime(TestCase):
    def test_start(self):
        summary = DowntimeSummary()
        downtime = Downtime(summary)
        downtime.start()
        self.assertIsInstance(downtime.start_date, datetime)
        self.assertIsNone(downtime.end_date)

    def test_start_and_end(self):
        summary = DowntimeSummary()
        downtime = Downtime(summary)
        downtime.start()
        self.assertIsInstance(downtime.start_date, datetime)
        time.sleep(1)
        downtime.finish()
        self.assertIsInstance(downtime.end_date, datetime)
        self.assertIsNone(downtime.start_date)
        self.assertEqual(len(summary.downtimes), 1)

    def test_get_duration_is_seconds(self):
        summary = DowntimeSummary()
        downtime = Downtime(summary)
        downtime.start()
        time.sleep(2)
        duration: int = downtime.finish()
        self.assertEqual(duration, 2)
