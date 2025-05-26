from unittest import TestCase
from freezegun import freeze_time
from datetime import datetime, timedelta
from typing import Dict

from sqlpinger.core.summary import DowntimeSummary


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
