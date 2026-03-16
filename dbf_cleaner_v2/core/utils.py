
import os
from datetime import datetime
from typing import Optional

try:
    import dbf  # type: ignore
except Exception:  # pragma: no cover
    dbf = None


def is_locked(path: str) -> bool:
    """Return True if file appears to be locked by another process.
    On Windows, opening rb+ will fail if another process holds a deny-write handle.
    """
    if not os.path.isfile(path):
        return False
    try:
        with open(path, 'rb+'):  # attempt write handle
            return False
    except Exception:
        return True


def find_dt_field(table) -> Optional[str]:
    for name in table.field_names:
        if name.upper() == 'DT':
            return name
    return None


def parse_dt(value) -> Optional[datetime]:
    if value is None:
        return None
    # Already datetime
    if isinstance(value, datetime):
        return value
    # xBase date-like with attributes year/month/day
    if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
        try:
            return datetime(int(value.year), int(value.month), int(value.day))
        except Exception:
            return None
    # Strings common patterns (last resort)
    if isinstance(value, str):
        value = value.strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                pass
    return None
