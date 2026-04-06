# Acadza AI Intern Assignment — Submission

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Windows one-command setup:

```powershell
.\run.ps1 -WithTests
```

## Project Structure

- `main.py` — FastAPI routes and error handlers only.
- `core/data_loader.py` — data loading + question normalization + data quality counters.
- `services/marks.py` — robust mark parsing and percentage conversion.
- `services/analysis.py` — student analytics and scoring components.
- `services/recommendation.py` — deterministic rule-based DOST planning.
- `services/questions.py` — question lookup and response shaping.
- `services/leaderboard.py` — final scoring and ranking.
- `schemas/models.py` — Pydantic response and error schemas.
- `tests/` — Pytest unit tests for parsing/analysis/recommendation/question lookup.

## Design Decisions (why I built it this way)

I kept business logic out of routes because this makes testing easier and avoids regression while iterating on recommendation rules. `main.py` is now thin, and each service has one responsibility. This is closer to production patterns.

I also made recommendation output deterministic. The same student profile always gets the same plan and question order, which is important for debugging and trust. I deliberately avoided random selection in question assignment.

Error handling uses a consistent schema:

```json
{
  "error": "HTTP_ERROR",
  "message": "Student 'STU_999' not found.",
  "status_code": 404
}
```

This makes frontend integration predictable and easier to debug.

## Data Understanding and Cleaning

The marks field is intentionally messy. I wrote `parse_marks()` to handle:

- `"39/100"` -> `39.0`
- `"+48 -8"` -> `40.0`
- `"49/120 (40.8%)"` -> `49.0`
- `"22"` / `22` -> `22.0`

Then `marks_to_percentage()` converts scores to percentage where a denominator exists. For `+X -Y`, I use `total_questions * 4` as max score (JEE Mains assumption).

Question bank data quality is explicitly tracked:

- duplicate `_id` skipped
- null difficulty defaulted to `3`
- missing answer counted and excluded from recommendations

These counts are exposed in `/analyze` as `bad_questions_ignored`.

## Analytics Logic (`/analyze/{student_id}`)

For each student, I compute:

- overall and chapter/subject score trends
- strengths and weaknesses
- completion behavior
- speed behavior (`speed_score` separate from accuracy)
- improvement score (last 3 attempts vs first 3 where possible)

This gives a richer profile than just raw average marks and reflects "how" a student is performing.

## Recommendation Logic (`/recommend/{student_id}`)

The plan is rule-based and explainable:

1. `concept` on weakest chapter
2. `formula` on same chapter
3. `practiceAssignment` (targeted, untimed)
4. `pickingPower` on second weakness
5. `clickingPower` if speed is poor
6. `revision` for retention
7. `practiceTest` for exam simulation
8. `speedRace` only if trend is improving

Question selection is deterministic by:

- unseen questions first (based on prior outlier question ids in attempts)
- best topic/subtopic match
- closest difficulty to target
- stable tie-breaker on question id

This avoids noisy recommendations and makes outputs reproducible.

## Question Lookup (`/question/{question_id}`)

Supports both `_id` forms:

- oid-like id (e.g. `d3b6e9...`)
- human-readable `qid` (e.g. `Q_CHE_0001`)

Returns detailed payload with subject/topic/subtopic/options/answer/preview/solution.

## Leaderboard (`/leaderboard`)

Ranking combines:

- average performance
- completion rate
- consistency (std dev based)
- improvement signal
- trend bonus (improving/stable/declining)

I preferred this over pure marks-only ranking because learning velocity and consistency are useful in an EdTech setting.

## Logging and Validation

- Added logging at key service points (`analyze` and `recommend`) to make runtime behavior observable.
- Added path-level validation and consistent error responses for invalid/missing IDs.

## Tests

Implemented Pytest tests for:

- mark parsing and percentage conversion
- analysis outputs and quality counters
- deterministic recommendation behavior
- question lookup by both qid and oid formats

Run:

```bash
pytest -q
```

## Sample API Responses (trimmed)

`POST /analyze/STU_001`

```json
{
  "student_id": "STU_001",
  "performance_trend": "improving",
  "accuracy_score": 52.8,
  "speed_score": 39.5,
  "weaknesses": ["Thermodynamics", "Electrostatics"]
}
```

`POST /recommend/STU_001`

```json
{
  "student_id": "STU_001",
  "recommendation_steps": [
    {"step": 1, "dost_type": "concept", "target_chapter": "Thermodynamics"},
    {"step": 2, "dost_type": "formula", "target_chapter": "Thermodynamics"},
    {"step": 3, "dost_type": "practiceAssignment", "question_ids": ["Q_PHY_0012", "Q_PHY_0042"]}
  ]
}
```

## Debug Process (`debug/recommender_buggy.py`)

The bug was a logical overwrite in profile normalization:

- buggy code normalized `cohort_baseline` and overwrote `student_profile`
- result: all students got nearly identical recommendations

Fixed version in `debug/recommender_fixed.py` correctly normalizes the personalized profile vector:

```python
profile_norm = np.linalg.norm(student_profile)
student_profile = student_profile / (profile_norm + 1e-10)
```

I validated by overlap analysis: recommendations became student-specific after the fix.

## Assumptions

- `+X -Y` marks use JEE Mains max score model (`total_questions * 4`).
- plain integer marks without denominator are treated as raw score; percentage conversion is skipped.
- difficulty is mapped numerically (1-5), with null defaulted to 3.

## If I Had 1 More Week

1. Add an embedding-based recommendation layer on top of rules.
2. Improve question difficulty estimation using student-level response history.
3. Add Redis caching for `/leaderboard` and heavy analytics.
4. Containerize with Docker and add CI checks (tests + lint + smoke API calls).
5. Persist recommendation execution state to prevent repetitive steps.
6. Add A/B metrics for recommendation quality (engagement + score lift).
