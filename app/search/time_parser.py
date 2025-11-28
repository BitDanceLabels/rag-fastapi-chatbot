from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_time_hint(hint: Optional[str]) -> Optional[Tuple[datetime, datetime]]:
    """
    Convert fuzzy time phrases to a concrete [start, end] UTC window.
    Examples: "tháng trước", "mấy hôm trước", "mùa đông năm ngoái", "tuần trước", "hôm nay", "hôm qua".
    Returns None if cannot parse.
    """
    if not hint:
        return None

    now = datetime.utcnow()
    text = hint.lower().strip()

    if "hôm nay" in text:
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
        return start, end

    if "hôm qua" in text:
        end = datetime(now.year, now.month, now.day)
        start = end - timedelta(days=1)
        return start, end

    if "mấy hôm" in text or "mấy ngày" in text:
        end = now
        start = now - timedelta(days=7)
        return start, end

    if "tuần trước" in text:
        end = now
        start = now - timedelta(days=14)
        return start, end

    if "tháng trước" in text:
        end = now
        start = now - timedelta(days=45)
        return start, end

    if "mùa đông năm ngoái" in text:
        year = now.year - 1
        start = datetime(year, 12, 1)
        end = datetime(year + 1, 3, 1)
        return start, end

    if "6 tháng" in text or "6m" in text:
        end = now
        start = now - timedelta(days=180)
        return start, end

    return None
