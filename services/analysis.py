import logging
from typing import Any

from services.marks import marks_to_percentage, parse_marks


logger = logging.getLogger(__name__)


def analyze_student(student: dict[str, Any], question_quality: dict[str, int]) -> dict[str, Any]:
    logger.info("Analyzing student=%s", student.get("student_id"))
    attempts = student.get("attempts", [])
    chapter_stats: dict[str, dict[str, Any]] = {}
    subject_stats: dict[str, dict[str, Any]] = {}
    completion_rates: list[float] = []
    all_pcts: list[float] = []
    speed_values: list[float] = []
    aborted_sessions = 0

    for att in attempts:
        pct = marks_to_percentage(att.get("marks"), att)
        if pct is not None:
            all_pcts.append(pct)

        if not att.get("completed", True):
            aborted_sessions += 1

        attempted = float(att.get("attempted", 0) or 0)
        total_q = float(att.get("total_questions", 1) or 1)
        completion_rates.append(attempted / total_q)

        avg_t = att.get("avg_time_per_question_seconds")
        if avg_t:
            speed_values.append(float(avg_t))

        subject = att.get("subject", "Unknown")
        subject_stats.setdefault(subject, {"attempts": 0, "scores": [], "chapters": set()})
        subject_stats[subject]["attempts"] += 1
        if pct is not None:
            subject_stats[subject]["scores"].append(pct)

        for ch in att.get("chapters", []):
            chapter_stats.setdefault(ch, {"attempts": 0, "scores": [], "subjects": set()})
            chapter_stats[ch]["attempts"] += 1
            chapter_stats[ch]["subjects"].add(subject)
            subject_stats[subject]["chapters"].add(ch)
            if pct is not None:
                chapter_stats[ch]["scores"].append(pct)

    chapter_breakdown: dict[str, Any] = {}
    for ch, stats in chapter_stats.items():
        avg = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else None
        chapter_breakdown[ch] = {
            "attempts": stats["attempts"],
            "avg_score_pct": round(avg, 1) if avg is not None else None,
            "subjects": sorted(stats["subjects"]),
        }

    subject_breakdown: dict[str, Any] = {}
    for subj, stats in subject_stats.items():
        avg = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else None
        subject_breakdown[subj] = {
            "attempts": stats["attempts"],
            "avg_score_pct": round(avg, 1) if avg is not None else None,
            "chapters_covered": sorted(stats["chapters"]),
        }

    chapter_scores = {
        ch: data["avg_score_pct"]
        for ch, data in chapter_breakdown.items()
        if data["avg_score_pct"] is not None
    }
    sorted_chapters = sorted(chapter_scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [ch for ch, _ in sorted_chapters[:3]]
    weaknesses = [ch for ch, _ in sorted(chapter_scores.items(), key=lambda x: x[1])[:3]]

    improvement_score = 0.0
    trend = "stable"
    if len(all_pcts) >= 6:
        first = sum(all_pcts[:3]) / 3
        last = sum(all_pcts[-3:]) / 3
        improvement_score = round(last - first, 1)
        trend = "improving" if improvement_score > 5 else "declining" if improvement_score < -5 else "stable"
    elif len(all_pcts) >= 2:
        improvement_score = round(all_pcts[-1] - all_pcts[0], 1)
        trend = "improving" if improvement_score > 5 else "declining" if improvement_score < -5 else "stable"

    overall_avg = round(sum(all_pcts) / len(all_pcts), 1) if all_pcts else None
    accuracy_score = overall_avg or 0.0
    avg_speed = (sum(speed_values) / len(speed_values)) if speed_values else 150.0
    speed_score = round(max(0.0, min(100.0, 100.0 - ((avg_speed - 60.0) / 2.0))), 1)

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "total_attempts": len(attempts),
        "aborted_sessions": aborted_sessions,
        "avg_completion_rate_pct": round((sum(completion_rates) / len(completion_rates) * 100), 1) if completion_rates else 0.0,
        "performance_trend": trend,
        "improvement_score_pct_points": improvement_score,
        "accuracy_score": round(accuracy_score, 1),
        "speed_score": speed_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "chapter_breakdown": chapter_breakdown,
        "subject_breakdown": subject_breakdown,
        "overall_avg_score_pct": overall_avg,
        "slow_session_count": len([s for s in speed_values if s > 150]),
        "fast_session_count": len([s for s in speed_values if s < 60]),
        "bad_questions_ignored": question_quality,
    }


def student_seen_questions(student: dict[str, Any]) -> set[str]:
    seen: set[str] = set()
    for att in student.get("attempts", []):
        for key in ("slowest_question_id", "fastest_question_id"):
            qid = att.get(key)
            if qid:
                seen.add(str(qid))
    return seen


def infer_difficulty_band(overall_avg_score_pct: float | None) -> tuple[int, str]:
    if overall_avg_score_pct is None or overall_avg_score_pct < 40:
        return 2, "easy"
    if overall_avg_score_pct < 65:
        return 3, "medium"
    return 4, "hard"


def to_raw_score_or_zero(marks: Any) -> float:
    val = parse_marks(marks)
    return 0.0 if val is None else float(val)

