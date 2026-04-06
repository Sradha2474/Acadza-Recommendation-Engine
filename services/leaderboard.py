import math
from typing import Any

from services.analysis import to_raw_score_or_zero
from services.marks import marks_to_percentage


def compute_score(student: dict[str, Any], analysis: dict[str, Any]) -> float:
    avg = analysis.get("overall_avg_score_pct") or 0.0
    completion = analysis.get("avg_completion_rate_pct") or 0.0
    improvement = analysis.get("improvement_score_pct_points") or 0.0
    trend = analysis.get("performance_trend", "stable")

    pcts = [marks_to_percentage(a.get("marks"), a) for a in student.get("attempts", [])]
    pcts = [p for p in pcts if p is not None]
    if len(pcts) >= 2:
        mean = sum(pcts) / len(pcts)
        std = math.sqrt(sum((p - mean) ** 2 for p in pcts) / len(pcts))
        consistency = max(0.0, 100.0 - std * 2.0)
    else:
        consistency = 50.0

    trend_bonus = {"improving": 8.0, "stable": 4.0, "declining": 0.0}.get(trend, 4.0)
    improvement_component = max(-10.0, min(10.0, improvement))
    score = (0.55 * avg) + (0.15 * completion) + (0.15 * consistency) + (0.10 * (50 + improvement_component)) + trend_bonus
    return round(score, 2)


def build_leaderboard(students: list[dict[str, Any]], analyses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    entries = []
    for student in students:
        sid = student["student_id"]
        analysis = analyses[sid]
        score = compute_score(student, analysis)
        entries.append(
            {
                "student_id": sid,
                "name": student["name"],
                "score": score,
                "overall_avg_pct": analysis.get("overall_avg_score_pct"),
                "strength": analysis["strengths"][0] if analysis["strengths"] else "N/A",
                "weakness": analysis["weaknesses"][0] if analysis["weaknesses"] else "N/A",
                "focus_area": analysis["weaknesses"][0] if analysis["weaknesses"] else "N/A",
                "trend": analysis["performance_trend"],
                "raw_marks_sum": round(sum(to_raw_score_or_zero(a.get("marks")) for a in student.get("attempts", [])), 1),
            }
        )
    entries.sort(key=lambda x: x["score"], reverse=True)
    for idx, row in enumerate(entries, start=1):
        row["rank"] = idx
    return {"leaderboard": entries}

