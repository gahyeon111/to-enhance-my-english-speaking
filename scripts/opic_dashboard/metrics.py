from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any


SCORE_LABELS = {
    "content": "내용",
    "grammar": "문법",
    "vocabulary": "표현",
    "flow": "흐름",
    "delivery": "전달력",
}


def _study_streak(study_days: list[date], today: date) -> int:
    if not study_days:
        return 0
    unique = sorted(set(study_days), reverse=True)
    if unique[0] not in {today, today - timedelta(days=1)}:
        return 0
    streak = 1
    for previous, current in zip(unique, unique[1:]):
        if previous - current != timedelta(days=1):
            break
        streak += 1
    return streak


def add_metrics(data: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    completed = [session for session in data["sessions"] if session.get("status") == "completed"]
    days = [datetime.strptime(session["date"], "%Y-%m-%d").date() for session in completed]
    score_totals: dict[str, list[int]] = {key: [] for key in SCORE_LABELS}
    mistake_totals: dict[str, dict[str, Any]] = {}
    mission_counts: Counter[str] = Counter()

    for session in completed:
        for key in SCORE_LABELS:
            value = session.get("scores", {}).get(key)
            if isinstance(value, int):
                score_totals[key].append(value)
        for mistake in session.get("mistakes", []):
            mistake_id = str(mistake.get("id", mistake.get("label", "unknown")))
            record = mistake_totals.setdefault(
                mistake_id,
                {"id": mistake_id, "label": mistake.get("label", mistake_id), "count": 0, "sessions": 0},
            )
            record["count"] += int(mistake.get("count", 1))
            record["sessions"] += 1
        mission_counts[str(session.get("mission", {}).get("result", "unknown"))] += 1

    completed_count = len(completed)
    remaining = 7 - (completed_count % 7) if completed_count % 7 else (0 if completed_count else 7)
    data["metrics"] = {
        "completed": completed_count,
        "study_days": len(set(days)),
        "streak": _study_streak(days, today),
        "weekly_review_remaining": remaining,
        "score_labels": SCORE_LABELS,
        "score_averages": {
            key: round(sum(values) / len(values), 1) if values else None for key, values in score_totals.items()
        },
        "mistakes": sorted(mistake_totals.values(), key=lambda item: (-item["count"], item["label"])),
        "missions": dict(mission_counts),
    }
    return data
