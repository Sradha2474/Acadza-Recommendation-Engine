"""
Generate sample outputs by calling the running FastAPI server.

Usage:
  python generate_outputs.py
  python generate_outputs.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DATA_DIR = Path(__file__).parent
STUDENTS_FILE = DATA_DIR / "student_performance.json"
OUTPUT_DIR = DATA_DIR / "sample_outputs"


def http_json(url: str, method: str = "GET") -> dict:
    try:
        req = Request(url=url, method=method.upper())
        with urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {method.upper()} {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not connect to server for {method.upper()} {url}") from exc


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    students = json.loads(STUDENTS_FILE.read_text(encoding="utf-8"))
    student_ids = [s["student_id"] for s in students]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for student_id in student_ids:
        analyze_url = f"{base_url}/analyze/{student_id}"
        recommend_url = f"{base_url}/recommend/{student_id}"

        analyze_data = http_json(analyze_url, method="POST")
        recommend_data = http_json(recommend_url, method="POST")

        save_json(OUTPUT_DIR / f"{student_id}_analyze.json", analyze_data)
        save_json(OUTPUT_DIR / f"{student_id}_recommend.json", recommend_data)
        print(f"Saved outputs for {student_id}")

    leaderboard_data = http_json(f"{base_url}/leaderboard", method="GET")
    save_json(OUTPUT_DIR / "leaderboard.json", leaderboard_data)
    print("Saved leaderboard.json")
    print(f"All files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
