# Solution Architecture: AI Receipt Digitizer

## 1. Overview

A single-page web app backed by a Python pipeline and a PostgreSQL database, all orchestrated with Docker Compose. The pipeline follows four layers, adapted from the original project outline.

```
[ Browser ]
    |  upload up to 5 images
    v
+---------------------------------------------------+
|  Streamlit app (app/main.py)                      |
|  - file uploader, data editor, pie chart          |
+-------------------------+-------------------------+
                          |
                          v
+---------------------------------------------------+
|  core/  (UI-independent business logic)           |
|  preprocess.py  -> OpenCV clean up                |
|  ocr.py         -> EasyOCR (CRAFT + CRNN)         |
|  extract.py     -> regex amount + category rules  |
|  db.py          -> PostgreSQL data access         |
+-------------------------+-------------------------+
                          |
                          v
+---------------------------------------------------+
|  PostgreSQL (docker service: db)                  |
+---------------------------------------------------+
```

The key architectural rule: **`core/` never imports Streamlit.** The UI calls into `core/`, not the other way around. This is what lets you swap Streamlit for a custom Flask + JS frontend after the demo without rewriting the AI or database logic.

## 2. The four layers

**Layer 1: Data ingestion.** Streamlit `file_uploader` with `accept_multiple_files=True`. Enforce the 5 file cap in code. Files stay in RAM as byte buffers.

**Layer 2: Image preprocessing (OpenCV).** For each image: decode to a numpy array, resize to ~900 px width keeping aspect ratio, convert to grayscale, apply adaptive threshold (`cv2.adaptiveThreshold`, Gaussian) to handle uneven receipt lighting better than a global threshold.

**Layer 3: Extraction and classification.** EasyOCR reads the cleaned image and returns text lines with confidence. `extract.py` then runs keyword anchored regex for the amount and a keyword dictionary for the category. Both are rule based and locale aware for Indonesian receipts.

**Layer 4: Persistence and visualization.** Confirmed rows are inserted into PostgreSQL. A `SUM ... GROUP BY category` query feeds a Plotly pie chart.

## 3. Tech stack and rationale

| Concern | Choice | Why | Cost |
|---|---|---|---|
| Language | Python 3.11 | Matches the AI ecosystem, one language end to end | Free |
| OCR / AI | EasyOCR (PyTorch CPU) | Deep learning OCR, runs local, no API key, defensible as "AI" | Free |
| Image CV | OpenCV (opencv-python-headless) | Standard preprocessing, headless build fits Docker | Free |
| Extraction | Python `re` + keyword dict | Simple, transparent, easy to defend and demo | Free |
| UI (MVP) | Streamlit | Built-in uploader, editable table (`st.data_editor`), Plotly support. Fastest path to a working demo | Free |
| Charts | Plotly | Interactive pie chart, integrates with Streamlit | Free |
| Database | PostgreSQL 16 | Industrial grade, clean in Docker, good thesis story | Free |
| DB driver | psycopg2-binary | Thin, reliable, no ORM overhead for this scope | Free |
| DB admin (optional) | pgAdmin | Only if the lecturer wants to inspect tables live | Free |
| Config | python-dotenv + `.env` | Keep credentials out of code and git | Free |
| Packaging | Docker + Docker Compose | One command to run, identical on both machines | Free |

Why not Tesseract: less accurate on photographed receipts and reads less like an "AI" contribution. Why not a cloud OCR API: violates the free and local requirements and adds a network dependency on demo day.

## 4. Why one repository (not two)

Use a **single monorepo**. Reasons:

- Small scope, two collaborators, one deliverable. Two repos add versioning and CORS coordination cost with no benefit here.
- Docker Compose orchestrates everything from one `docker-compose.yml`, so it wants one root.
- For the MVP the UI is Streamlit, so there is no separate frontend service to isolate.
- A self-contained repo is easier to clone, demo, and grade.

Folder separation inside the one repo gives you clean boundaries without repo overhead. If you later add a custom Flask + JS frontend, add a `web/` folder in the same repo and reuse `core/`. Only split into a second repo if the frontend ever grows its own build pipeline and deploy cadence, which is unlikely for a thesis.

## 5. Repository structure

```
receipt-digitizer/
├── CLAUDE.md               # context for claude-cli
├── README.md               # setup + run instructions
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── ACTION_PLAN.md
├── app/
│   ├── main.py             # Streamlit UI only
│   ├── config.py           # loads .env
│   └── core/
│       ├── __init__.py
│       ├── preprocess.py   # OpenCV
│       ├── ocr.py          # EasyOCR wrapper
│       ├── extract.py      # regex amount + category rules
│       └── db.py           # PostgreSQL access
├── tests/
│   ├── sample_receipts/    # real photos for the demo
│   └── test_extract.py     # unit tests for regex, no OCR needed
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 6. Data model

Single table for the MVP. Keep it flat.

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL PRIMARY KEY,
    source_file TEXT,
    merchant    TEXT,
    category    TEXT NOT NULL DEFAULT 'Uncategorised',
    amount      NUMERIC(14,2) NOT NULL,
    raw_text    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`raw_text` is kept for auditability and makes a good talking point in the defense (you can show what the OCR saw versus what was saved).

## 7. Docker architecture

Two required services plus one optional.

- `app`: builds from the Dockerfile, runs Streamlit on 8501, depends on `db`.
- `db`: official `postgres:16` image, data on a named volume so records survive restarts.
- `pgadmin` (optional): behind a Compose profile so it does not start unless asked.

OCR models are downloaded at **image build time** and baked in, so the demo runs with no internet.

## 8. Key implementation notes

**EasyOCR init:** create the `Reader` once at app startup, not per image. In Streamlit, cache it with `@st.cache_resource` so it is not reloaded on every rerun. Use `Reader(['en'], gpu=False)`. Indonesian receipts are mostly Latin characters and digits, so English works; add `'id'` only if needed.

**Adaptive threshold beats global** on receipts with shadows or creases:
```python
cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                      cv2.THRESH_BINARY, 31, 10)
```

**Indonesian amount regex.** Numbers use a dot as the thousands separator (`Rp 25.000` means twenty five thousand). Anchor on keywords and take the largest matched value on the receipt as a fallback total:
```python
KEYWORDS = r'(grand\s*total|total\s*belanja|total|tunai|bayar|netto)'
# find "Rp" optional, then digits with . or , separators
AMOUNT = r'(?:rp\.?\s*)?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)'
```
Normalise by stripping thousands dots before converting to a number. Guard against reading the change / kembalian as the total by preferring lines that contain a total keyword.

**Category dictionary (starter):**
```python
CATEGORIES = {
    "Groceries":  ["alfamart", "indomaret", "superindo", "hypermart", "giant"],
    "F&B":        ["kopi", "coffee", "resto", "cafe", "kfc", "mcd", "warung"],
    "Transport":  ["grab", "gojek", "pertamina", "shell", "spbu", "mrt"],
    "Pharmacy":   ["apotek", "kimia farma", "guardian", "watsons"],
}
```
Match against the lowercased full OCR text. First match wins; default to `Uncategorised`.

## 9. Configuration and secrets

All credentials come from `.env` (git ignored). Ship `.env.example` with safe placeholders. `app/config.py` reads them with `python-dotenv`. Inside Docker, the DB host is the service name `db`, not `localhost`.

## 10. Deployment plan (post-demo)

Because everything is already dockerized, the cleanest path is to run the same `docker-compose.yml` on a small VPS.

- **Recommended:** a small VPS (for example Hetzner, DigitalOcean, or Contabo, roughly a few dollars a month). Install Docker, clone the repo, `docker compose up -d`, point a domain or use the IP. This matches your local stack exactly, which is the whole point of dockerizing.
- **Fully free alternative:** Streamlit Community Cloud for the app (public repo required, ~1 GB RAM, tight but workable for light OCR use) plus a free managed Postgres such as Neon or Supabase for the database. Trade off: you lose the single-command parity and split the stack.

Given your note that a small server cost is acceptable, the single-VPS route is simpler and more faithful to the architecture. Do not expose PostgreSQL to the public internet; keep it on the Docker network and only publish the app port.

## 11. Future work (thesis "future work" section)

- Trained category classifier to replace the keyword dictionary.
- Perspective correction / deskew for angled photos.
- Line-item level extraction, not just totals.
- Multi-user accounts and auth.
- Swap EasyOCR for PaddleOCR and benchmark accuracy on Indonesian receipts.
