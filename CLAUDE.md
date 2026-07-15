# CLAUDE.md

Context for automated coding on this project. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/ACTION_PLAN.md` before making changes.

## What this is

A local-first web app that turns up to 5 receipt photos into a categorised expense record with a live pie chart. It is a bachelor thesis demo. Deadline driven, so favour a working end-to-end path over polish.

## Stack

- Python 3.11
- Streamlit for the UI (MVP)
- EasyOCR (PyTorch CPU) for OCR, this is the deep learning component
- OpenCV (opencv-python-headless) for preprocessing
- Python `re` for amount extraction, keyword dictionary for categories (rule based)
- PostgreSQL 16 via psycopg2-binary
- Plotly for the chart
- Docker + Docker Compose for packaging

## Golden rules

1. **`core/` must never import Streamlit or any UI code.** The UI depends on `core/`, never the reverse. This keeps a future Flask frontend possible.
2. **Do not overclaim ML.** OCR is machine learning. Amount extraction and categorisation are rule based. Comments and any user-facing text must reflect that honestly.
3. **Indonesian number format:** a dot is the thousands separator (`25.000` is twenty five thousand). Normalise before converting to a number. Do not treat change / `kembali` as the total.
4. **Secrets live in `.env`,** which is git ignored. Never hardcode credentials. Inside Docker the DB host is `db`, not `localhost`.
5. **Load the EasyOCR Reader once.** In Streamlit use `@st.cache_resource`. Never construct a Reader per image or per rerun.
6. Keep it simple. No ORM, no auth, no extra services for the MVP.

## Project layout

```
app/main.py          Streamlit UI only
app/config.py        loads .env
app/core/preprocess.py   OpenCV clean up
app/core/ocr.py          EasyOCR wrapper
app/core/extract.py      regex amount + category rules
app/core/db.py           PostgreSQL access
tests/test_extract.py    unit tests for extraction, no OCR needed
```

## Commands

```bash
# unit tests (no OCR, no DB needed)
python -m pytest

# full app locally
docker compose up --build

# with pgAdmin for DB inspection
docker compose --profile admin up
```

## Data model

Single `transactions` table: id, source_file, merchant, category, amount NUMERIC(14,2), raw_text, created_at. Schema is created on startup by `db.init_schema()`.

## When writing code

- Small, focused, phase-aligned commits. See the action plan's commit rhythm.
- Add or update `tests/test_extract.py` whenever the regex or category logic changes.
- Prefer standard library and the listed dependencies. Do not add new dependencies without a clear reason.
- Keep functions small and typed where practical.
