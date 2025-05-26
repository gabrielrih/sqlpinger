import json
from datetime import datetime
from typing import List, Dict


class DowntimeSummary:
    def __init__(self):
        self.downtimes: List[Dict[str, str]] = []

    def record(self, start: datetime, end: datetime) -> None:
        duration = (end - start).total_seconds()
        self.downtimes.append({
            "from": start.strftime("%Y-%m-%d %H:%M:%S"),
            "to": end.strftime("%Y-%m-%d %H:%M:%S"),
            "time": f"{duration:.0f} seconds"
        })

    def __str__(self):
        summary: Dict = self.to_dict()
        return json.dumps(summary, indent = 4)

    def to_dict(self):
        total_downtime_seconds = sum(
            int(entry["time"].split()[0]) for entry in self.downtimes
        )
        return {
            "summary": {
                "downtimes_quantity": len(self.downtimes),
                "total_downtime": f"{total_downtime_seconds} seconds"
            },
            "downtimes": self.downtimes
        }
