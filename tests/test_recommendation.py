from core.data_loader import load_data
from services.analysis import analyze_student
from services.recommendation import build_recommendation_plan


def test_recommendation_is_deterministic() -> None:
    data = load_data()
    student = data["students_map"]["STU_001"]
    analysis = analyze_student(student, data["question_quality"])
    first = build_recommendation_plan(student, analysis, data["questions"], data["dost_config"])
    second = build_recommendation_plan(student, analysis, data["questions"], data["dost_config"])
    assert first["recommendation_steps"] == second["recommendation_steps"]


def test_recommendation_has_steps() -> None:
    data = load_data()
    student = data["students_map"]["STU_002"]
    analysis = analyze_student(student, data["question_quality"])
    plan = build_recommendation_plan(student, analysis, data["questions"], data["dost_config"])
    assert len(plan["recommendation_steps"]) >= 5

