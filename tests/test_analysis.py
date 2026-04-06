from core.data_loader import load_data
from services.analysis import analyze_student


def test_analyze_student_has_strengths_and_weaknesses() -> None:
    data = load_data()
    student = data["students_map"]["STU_001"]
    analysis = analyze_student(student, data["question_quality"])
    assert analysis["student_id"] == "STU_001"
    assert isinstance(analysis["strengths"], list)
    assert isinstance(analysis["weaknesses"], list)
    assert "accuracy_score" in analysis
    assert "speed_score" in analysis


def test_analyze_has_bad_question_stats() -> None:
    data = load_data()
    student = data["students"][0]
    analysis = analyze_student(student, data["question_quality"])
    assert "bad_questions_ignored" in analysis
    assert "missing_answer" in analysis["bad_questions_ignored"]

