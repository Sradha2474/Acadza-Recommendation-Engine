from core.data_loader import load_data
from services.questions import lookup_question, question_response_payload


def test_lookup_question_by_qid() -> None:
    data = load_data()
    q = lookup_question("Q_CHE_0001", data["questions_map"])
    assert q is not None
    payload = question_response_payload(q)
    assert payload["subject"] == "Chemistry"
    assert "preview" in payload


def test_lookup_question_by_oid_like_id() -> None:
    data = load_data()
    q = lookup_question("d3b6e9e8325916a427bc1985", data["questions_map"])
    assert q is not None
    assert q["qid"] == "Q_CHE_0001"

