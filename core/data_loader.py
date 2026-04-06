import json
import logging
import re
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parent.parent


def _strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:300]


def _normalize_question_id(raw_id: Any) -> str:
    if isinstance(raw_id, dict):
        return str(raw_id.get("$oid", raw_id))
    return str(raw_id)


def _extract_answer(raw_q: dict[str, Any]) -> str | None:
    for qtype in ("scq", "mcq", "integerQuestion"):
        block = raw_q.get(qtype) or {}
        if block:
            return block.get("answer")
    return None


def _extract_question_text(raw_q: dict[str, Any]) -> str:
    for qtype in ("scq", "mcq", "integerQuestion"):
        block = raw_q.get(qtype) or {}
        if block.get("question"):
            return str(block["question"])
    return ""


def _extract_options(raw_q: dict[str, Any], qtype: str) -> list[str]:
    block = raw_q.get(qtype) or {}
    html = str(block.get("question", ""))
    if not html:
        return []
    # Split option labels from html lines "(A) ... <br /> (B) ..."
    parts = re.findall(r"\(([A-D])\)\s*([^<]+)", html)
    return [f"{label}) {txt.strip()}" for label, txt in parts]


def load_data() -> dict[str, Any]:
    with open(DATA_DIR / "student_performance.json", encoding="utf-8") as f:
        students: list[dict[str, Any]] = json.load(f)
    with open(DATA_DIR / "question_bank.json", encoding="utf-8") as f:
        questions_raw: list[dict[str, Any]] = json.load(f)
    with open(DATA_DIR / "dost_config.json", encoding="utf-8") as f:
        dost_config: dict[str, Any] = json.load(f)

    qid_map: dict[str, dict[str, Any]] = {}
    questions: list[dict[str, Any]] = []
    students_map = {s["student_id"]: s for s in students}

    seen_oids: set[str] = set()
    bad_questions_ignored = {
        "duplicate_id": 0,
        "missing_answer": 0,
        "null_difficulty_defaulted": 0,
    }

    for raw_q in questions_raw:
        oid = _normalize_question_id(raw_q.get("_id"))
        if oid in seen_oids:
            bad_questions_ignored["duplicate_id"] += 1
            continue
        seen_oids.add(oid)

        diff = raw_q.get("difficulty")
        if diff is None:
            bad_questions_ignored["null_difficulty_defaulted"] += 1
            diff = 3

        qtype = str(raw_q.get("questionType", "scq"))
        answer = _extract_answer(raw_q)
        if answer is None:
            bad_questions_ignored["missing_answer"] += 1

        full = {
            "id": oid,
            "qid": raw_q.get("qid", oid),
            "question_type": qtype,
            "subject": raw_q.get("subject", ""),
            "topic": raw_q.get("topic", ""),
            "subtopic": raw_q.get("subtopic", ""),
            "difficulty": int(diff),
            "question_html": _extract_question_text(raw_q),
            "options": _extract_options(raw_q, qtype),
            "answer": answer,
            "solution": (raw_q.get(qtype) or {}).get("solution"),
            "preview": _strip_html(_extract_question_text(raw_q)),
            "has_answer": answer is not None,
        }
        questions.append(full)
        qid_map[oid] = full
        qid_map[full["qid"]] = full

    logger.info(
        "Loaded data: students=%s questions=%s ignored=%s",
        len(students),
        len(questions),
        bad_questions_ignored,
    )
    return {
        "students": students,
        "students_map": students_map,
        "questions": questions,
        "questions_map": qid_map,
        "dost_config": dost_config,
        "question_quality": bad_questions_ignored,
    }

