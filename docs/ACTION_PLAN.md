# Action Plan: from empty folder to Wednesday demo

This plan is ordered so that the app works end to end as early as possible, then gets polished. Each phase has an acceptance check. Feed one phase at a time to claude-cli.

## Phase 0: Scaffold and git identity (30 to 45 min)

Set the repo up with your personal identity from the first commit.

```bash
mkdir receipt-digitizer && cd receipt-digitizer
git init
git config user.name "Daffa Pradana"
git config user.email "daffaarravi@gmail.com"
git config user.email      # verify it prints the personal address
```

This sets identity per repo (local), so it overrides your global work email for this project only. Since both emails already sit on the same GitHub account, commits still link to your profile, they just carry the personal address. Create the GitHub repo under github.com/daffa-pradana, add the remote, and push once the skeleton exists.

Then create the files below.

### requirements.txt
```
streamlit
easyocr
opencv-python-headless
numpy
pillow
plotly
pandas
psycopg2-binary
python-dotenv
```

### .env.example
```
POSTGRES_USER=receipt
POSTGRES_PASSWORD=change_me
POSTGRES_DB=receipts
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### .gitignore
```
__pycache__/
*.pyc
.env
.venv/
venv/
tests/sample_receipts/*.jpg
tests/sample_receipts/*.png
.DS_Store
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

# OpenCV runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch first to avoid pulling CUDA wheels
RUN pip install --no-cache-dir torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake OCR models into the image so the demo needs no internet
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"

COPY app/ ./app/

EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

### docker-compose.yml
```yaml
services:
  app:
    build: .
    ports:
      - "8501:8501"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16
    env_file: .env
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4
    profiles: ["admin"]
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.test
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"

volumes:
  pgdata:
```

**Acceptance:** `git config user.email` shows the personal email, and all scaffold files exist. Do not run the heavy build yet.

## Phase 1: Core pipeline, testable offline (2 to 3 hours)

Build `core/` so it runs on a sample image with no UI and no database.

- `preprocess.py`: `clean(image_bytes) -> numpy array` doing decode, resize, grayscale, adaptive threshold.
- `ocr.py`: `read(image) -> (full_text, lines_with_conf)` wrapping EasyOCR. Load the Reader once at module level or via a getter.
- `extract.py`: `extract(full_text) -> {merchant, category, amount, confidence}` using the regex and dictionary from the architecture doc.

Write `tests/test_extract.py` with fixed OCR-text strings (no image needed) to verify the regex handles `Rp 25.000`, `Total Belanja 150.000`, and does not pick up `Kembali` / change as the total.

**Acceptance:** `python -m pytest` passes on the extraction tests, and a quick script prints a sensible amount and category for one real receipt photo.

## Phase 2: Database layer (1 hour)

- `db.py`: `init_schema()`, `insert_transactions(rows)`, `spending_by_category() -> list of (category, total)`.
- Create the `transactions` table from the architecture doc on startup.
- Read connection settings from `config.py`.

**Acceptance:** running against the Dockerised Postgres, an insert then a `spending_by_category()` call returns the expected totals.

## Phase 3: Streamlit UI (2 to 3 hours)

`app/main.py` wires it together:

1. Title and a short intro.
2. `st.file_uploader(accept_multiple_files=True)`; block more than 5 files.
3. On upload, run each file through preprocess to ocr to extract, collect rows into a DataFrame.
4. Show `st.data_editor(df)` so the user can correct merchant, category, amount.
5. A Save button that calls `db.insert_transactions(...)`.
6. Below it, query `spending_by_category()` and draw a Plotly pie chart.
7. Cache the EasyOCR Reader with `@st.cache_resource`.

**Acceptance:** upload to edit to save to chart works entirely in the browser.

## Phase 4: Dockerize and full run (1 hour)

- `docker compose up --build` (do this the night before, the build is large).
- Verify the app reaches Postgres using host `db`, and models are baked in (disconnect wifi and confirm OCR still runs).

**Acceptance:** a fresh `docker compose up` on a clean checkout brings up a working app.

## Phase 5: Demo prep (30 min)

- Put 5 real, varied receipts in `tests/sample_receipts/`.
- Do a full dry run and note which receipts read cleanly.
- Prepare a one line answer for the honest AI framing (OCR is the ML part; extraction is rule based; the editable table handles OCR errors).
- **Fallback plan:** if the live build misbehaves, have the app already running in a terminal before you present, and keep one screen recording of a successful run as insurance.

**Acceptance:** you can run the full flow start to finish in under two minutes.

## Phase 6: Deployment (after the demo)

- Provision a small VPS, install Docker, clone the repo, copy `.env`, `docker compose up -d`.
- Publish only port 8501; keep Postgres on the internal Docker network.
- Optionally add the custom Flask + JS frontend in a `web/` folder, reusing `core/` untouched.

## Suggested commit rhythm

Small, phase-aligned commits: `chore: scaffold + docker`, `feat: core preprocessing`, `feat: ocr wrapper`, `feat: rule-based extraction + tests`, `feat: postgres layer`, `feat: streamlit ui`, `docs: readme`. Your brother pulls after each pushed phase so you are never merging large diffs.
