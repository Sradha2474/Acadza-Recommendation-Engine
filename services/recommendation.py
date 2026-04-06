import logging
from typing import Any

from services.analysis import infer_difficulty_band, student_seen_questions


logger = logging.getLogger(__name__)


def _topic_match_score(chapter: str, q: dict[str, Any]) -> int:
    key = chapter.lower().replace(" ", "_")
    score = 0
    if key in str(q.get("topic", "")).lower():
        score += 2
    if key in str(q.get("subtopic", "")).lower():
        score += 2
    if chapter.lower() in str(q.get("qid", "")).lower():
        score += 1
    return score


def pick_questions_deterministic(
    chapter: str,
    subject: str,
    target_difficulty: int,
    questions: list[dict[str, Any]],
    seen_qids: set[str],
    n: int,
) -> list[str]:
    candidates = [
        q
        for q in questions
        if q["subject"].lower() == subject.lower() and q.get("has_answer", False)
    ]
    if not candidates:
        return []

    def sort_key(q: dict[str, Any]) -> tuple[int, int, int, str]:
        seen_penalty = 1 if q["qid"] in seen_qids or q["id"] in seen_qids else 0
        topic_score = _topic_match_score(chapter, q)
        diff_distance = abs(int(q["difficulty"]) - target_difficulty)
        return (seen_penalty, -topic_score, diff_distance, str(q["qid"]))

    ranked = sorted(candidates, key=sort_key)
    selected = [q["qid"] for q in ranked[:n]]
    return list(dict.fromkeys(selected))


def build_recommendation_plan(
    student: dict[str, Any],
    analysis: dict[str, Any],
    questions: list[dict[str, Any]],
    dost_config: dict[str, Any],
) -> dict[str, Any]:
    logger.info("Generating recommendation for student=%s", student["student_id"])
    weaknesses = analysis.get("weaknesses", [])
    strengths = analysis.get("strengths", [])
    subject_scores = {
        s: v["avg_score_pct"]
        for s, v in analysis.get("subject_breakdown", {}).items()
        if v["avg_score_pct"] is not None
    }
    weakest_subject = min(subject_scores, key=subject_scores.get) if subject_scores else "Physics"
    best_subject = max(subject_scores, key=subject_scores.get) if subject_scores else "Physics"
    diff_level, diff_label = infer_difficulty_band(analysis.get("overall_avg_score_pct"))
    seen_qids = student_seen_questions(student)
    steps: list[dict[str, Any]] = []

    def add_step(
        dost_type: str,
        target_chapter: str,
        subject: str,
        reasoning: str,
        message: str,
        params: dict[str, Any] | None = None,
        question_ids: list[str] | None = None,
    ) -> None:
        config = (dost_config.get(dost_type) or {}).copy()
        payload_params = config.get("params", {})
        if params:
            payload_params.update(params)
        steps.append(
            {
                "step": len(steps) + 1,
                "dost_type": dost_type,
                "target_chapter": target_chapter,
                "subject": subject,
                "params": payload_params,
                "question_ids": question_ids or [],
                "reasoning": reasoning,
                "message_to_student": message,
            }
        )

    if weaknesses:
        ch = weaknesses[0]
        add_step(
            "concept",
            ch,
            weakest_subject,
            "Start with fundamentals on the weakest chapter to reduce conceptual errors.",
            f"Start with concept revision for {ch}. Build a strong base first.",
        )
        add_step(
            "formula",
            ch,
            weakest_subject,
            "Formula pass right after concept revision improves recall speed.",
            f"Now revise formulas for {ch} so you can solve faster.",
        )
        add_step(
            "practiceAssignment",
            ch,
            weakest_subject,
            "Untimed targeted practice improves method accuracy before speed pressure.",
            f"Solve this focused assignment on {ch} with full attention to method.",
            params={"difficulty": diff_label},
            question_ids=pick_questions_deterministic(ch, weakest_subject, diff_level, questions, seen_qids, n=8),
        )

    if len(weaknesses) >= 2:
        ch2 = weaknesses[1]
        add_step(
            "pickingPower",
            ch2,
            weakest_subject,
            "Option-elimination drill improves decision quality in MCQ settings.",
            f"Practice elimination strategy on {ch2} to avoid negative marking.",
            question_ids=pick_questions_deterministic(ch2, weakest_subject, max(1, diff_level - 1), questions, seen_qids, n=5),
        )

    if analysis.get("slow_session_count", 0) >= 2:
        ch3 = weaknesses[0] if weaknesses else "Mixed"
        add_step(
            "clickingPower",
            ch3,
            weakest_subject,
            "Speed drill triggered because multiple sessions show high average time/question.",
            "Do this timed speed drill to increase pace without losing accuracy.",
            params={"total_questions": 10},
            question_ids=pick_questions_deterministic(ch3, weakest_subject, max(1, diff_level - 1), questions, seen_qids, n=10),
        )

    if weaknesses:
        add_step(
            "revision",
            weaknesses[0],
            weakest_subject,
            "Spaced revision after practice stabilizes long-term retention.",
            f"Follow this short revision plan for {weaknesses[0]} over 3 days.",
            params={"alloted_days": 3},
        )

    focus = ", ".join(weaknesses[:2]) if weaknesses else "mixed topics"
    add_step(
        "practiceTest",
        f"Mixed (focus: {focus})",
        weakest_subject,
        "Timed test validates if concept + practice improvements transfer to exam conditions.",
        "Take this mock test in one sitting and review all mistakes afterward.",
        params={"difficulty": diff_label, "duration_minutes": 60},
        question_ids=pick_questions_deterministic(focus, weakest_subject, diff_level, questions, seen_qids, n=10),
    )

    if analysis.get("performance_trend") == "improving" and strengths:
        best = strengths[0]
        add_step(
            "speedRace",
            best,
            best_subject,
            "Confidence booster on strongest chapter reinforces momentum.",
            f"You are improving; attempt a speed race on {best}.",
            question_ids=pick_questions_deterministic(best, best_subject, min(5, diff_level + 1), questions, seen_qids, n=5),
        )

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "recommendation_steps": steps,
        "summary": f"Rule-based plan prioritizes weaknesses first, then speed, then exam simulation. Focus: {focus}.",
    }

