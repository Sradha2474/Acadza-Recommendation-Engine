from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int


class AnalyzeResponse(BaseModel):
    student_id: str
    name: str
    total_attempts: int
    aborted_sessions: int
    avg_completion_rate_pct: float
    performance_trend: str
    improvement_score_pct_points: float
    accuracy_score: float
    speed_score: float
    strengths: list[str]
    weaknesses: list[str]
    chapter_breakdown: dict[str, Any]
    subject_breakdown: dict[str, Any]
    overall_avg_score_pct: float | None
    slow_session_count: int
    fast_session_count: int
    bad_questions_ignored: dict[str, int]


class RecommendationStep(BaseModel):
    step: int
    dost_type: str
    target_chapter: str
    subject: str
    params: dict[str, Any] = Field(default_factory=dict)
    question_ids: list[str] = Field(default_factory=list)
    reasoning: str
    message_to_student: str


class RecommendResponse(BaseModel):
    student_id: str
    name: str
    recommendation_steps: list[RecommendationStep]
    summary: str


class QuestionResponse(BaseModel):
    id: str
    qid: str
    question_type: str
    subject: str
    topic: str
    subtopic: str
    difficulty: int
    options: list[str]
    answer: str | None
    preview: str
    solution: str | None


class LeaderboardResponse(BaseModel):
    leaderboard: list[dict[str, Any]]

