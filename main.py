import logging

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.data_loader import load_data
from schemas.models import (
    AnalyzeResponse,
    ErrorResponse,
    LeaderboardResponse,
    QuestionResponse,
    RecommendResponse,
)
from services.analysis import analyze_student
from services.leaderboard import build_leaderboard
from services.questions import lookup_question, question_response_payload
from services.recommendation import build_recommendation_plan


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Acadza Recommender API", version="2.0.0")
DATA = load_data()


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    body = ErrorResponse(error="HTTP_ERROR", message=str(exc.detail), status_code=exc.status_code).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    body = ErrorResponse(error="VALIDATION_ERROR", message=str(exc.errors()), status_code=400).model_dump()
    return JSONResponse(status_code=400, content=body)


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    body = ErrorResponse(error="INTERNAL_ERROR", message="Internal server error", status_code=500).model_dump()
    return JSONResponse(status_code=500, content=body)


@app.get("/")
def home() -> dict[str, object]:
    return {
        "message": "Acadza Recommender API is running.",
        "docs": "/docs",
        "endpoints": ["/analyze/{student_id}", "/recommend/{student_id}", "/question/{question_id}", "/leaderboard"],
    }


@app.post(
    "/analyze/{student_id}",
    response_model=AnalyzeResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def analyze(student_id: str = Path(..., pattern=r"^STU_\d{3}$")) -> AnalyzeResponse:
    student = DATA["students_map"].get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    result = analyze_student(student, DATA["question_quality"])
    return AnalyzeResponse(**result)


@app.post(
    "/recommend/{student_id}",
    response_model=RecommendResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def recommend(student_id: str = Path(..., pattern=r"^STU_\d{3}$")) -> RecommendResponse:
    student = DATA["students_map"].get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    analysis = analyze_student(student, DATA["question_quality"])
    plan = build_recommendation_plan(student, analysis, DATA["questions"], DATA["dost_config"])
    return RecommendResponse(**plan)


@app.get(
    "/question/{question_id}",
    response_model=QuestionResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_question(question_id: str = Path(..., min_length=4)) -> QuestionResponse:
    q = lookup_question(question_id, DATA["questions_map"])
    if not q:
        raise HTTPException(status_code=404, detail=f"Question '{question_id}' not found.")
    return QuestionResponse(**question_response_payload(q))


@app.get("/leaderboard", response_model=LeaderboardResponse)
def leaderboard() -> LeaderboardResponse:
    analyses = {
        s["student_id"]: analyze_student(s, DATA["question_quality"])
        for s in DATA["students"]
    }
    return LeaderboardResponse(**build_leaderboard(DATA["students"], analyses))
