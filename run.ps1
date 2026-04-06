param(
  [switch]$WithTests = $false
)

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

if ($WithTests) {
  pytest -q
}

uvicorn main:app --reload --host 127.0.0.1 --port 8000

