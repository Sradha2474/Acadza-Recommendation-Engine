from typing import Any


def lookup_question(question_id: str, questions_map: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return questions_map.get(question_id)


def question_response_payload(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": question["id"],
        "qid": question["qid"],
        "question_type": question["question_type"],
        "subject": question["subject"],
        "topic": question["topic"],
        "subtopic": question["subtopic"],
        "difficulty": question["difficulty"],
        "options": question.get("options", []),
        "answer": question.get("answer"),
        "preview": question.get("preview", ""),
        "solution": question.get("solution"),
    }

