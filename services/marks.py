import re
from typing import Any


def parse_marks(raw: Any) -> float | None:
    """Parse all known marks formats into a numeric raw score."""
    if raw is None:
        return None
    s = str(raw).strip()
    try:
        return float(s)
    except ValueError:
        pass

    plus_minus = re.match(r"^\+?(\d+(?:\.\d+)?)\s*-(\d+(?:\.\d+)?)$", s)
    if plus_minus:
        return float(plus_minus.group(1)) - float(plus_minus.group(2))

    fraction = re.match(r"^(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", s)
    if fraction:
        return float(fraction.group(1))

    return None


def marks_to_percentage(raw: Any, attempt: dict[str, Any]) -> float | None:
    """Convert score format to percentage where denominator is available."""
    score = parse_marks(raw)
    if score is None:
        return None
    s = str(raw).strip()

    fraction = re.match(r"^(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", s)
    if fraction:
        denominator = float(fraction.group(2))
        return round((score / denominator) * 100, 1) if denominator else None

    embedded_pct = re.search(r"\((\d+(?:\.\d+)?)%\)", s)
    if embedded_pct:
        return float(embedded_pct.group(1))

    plus_minus = re.match(r"^\+?(\d+(?:\.\d+)?)\s*-(\d+(?:\.\d+)?)$", s)
    if plus_minus:
        total_questions = attempt.get("total_questions", 25) or 25
        max_score = float(total_questions) * 4.0
        return round((score / max_score) * 100, 1)

    return None

