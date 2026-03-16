
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class AnalysisResult:
    path: str
    dt_column: str
    total: int
    marked_total: int
    to_recall_indexes: List[int]
    to_remove_count: int
    not_marked_count: int
    parse_fail_count: int
    min_dt: Optional[datetime]
    max_dt: Optional[datetime]

    @property
    def remaining_after_cleanup(self) -> int:
        return len(self.to_recall_indexes) + self.not_marked_count
