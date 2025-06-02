import json
from datetime import datetime
from typing import List, Dict, Optional

from sqlpinger.util.logger import Logger


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


class Downtime:
    def __init__(self, summary: Optional[DowntimeSummary] = None):
        self.start_date = None
        self.end_date = None
        self.summary = summary if summary else DowntimeSummary()
        self.logger = Logger.get_logger(__name__)

    def start(self):
        if self.is_active():  # downtime already started
            return
        self.start_date = datetime.now()
        self.end_date = None

    def is_active(self) -> bool:
        return self.start_date is not None
    
    def finish(self) -> Optional[int]:
        if not self.is_active():
            return
        self.end_date = datetime.now()
        self.summary.record(self.start_date, self.end_date)
        duration: float = duration_in_seconds(self.start_date, self.end_date)
        self.start_date = None
        return int(duration)


def duration_in_seconds(start_date: datetime, end_date: datetime) -> float:
    return (end_date - start_date).total_seconds()
