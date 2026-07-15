# Action Plan & Progress Tracker

This is the shared source of truth for what's done and what's left. Check items off as they land on `main` (i.e. once their PR is merged), so both of you stay in sync without needing a separate status meeting. Update the **Current status** table whenever a phase's state changes.

Status legend: `[x]` done · `(in progress)` next to a phase title means actively being worked · unmarked phases haven't started.

## Current status

Split rationale: Daffa owns everything that needs Docker/WSL/Python fluency to build or debug. siapahayooo1709 owns demo-day legwork, PR review, and small self-contained content contributions (e.g. the category dictionary) that don't need git/terminal at all — see his phases for how.

| Phase | Owner | Status |
|---|---|---|
| 0: Scaffold, git identity, PR workflow | Daffa | ✅ Done |
| 1: Core pipeline (preprocess/OCR/extract) | Daffa | 🔄 In progress |
| 2: Database layer | Daffa | ⬜ Not started |
| 3: Streamlit UI | Daffa | ⬜ Not started |
| 4: Dockerize and full run | Daffa | ⬜ Not started |
| 5: Demo prep | siapahayooo1709 | ⬜ Not started |
| 6: Deployment (post-demo) | Daffa | ⬜ Not started |

**Ongoing (not phase-bound):** siapahayooo1709 reviews/approves every PR; he can also update the `CATEGORIES` dict in `app/core/extract.py` directly via GitHub's web "Edit this file" button (opens a PR for him automatically, no git/terminal needed) whenever he thinks of an Indonesian merchant keyword that's missing.

---

## Phase 0: Scaffold, git identity, PR workflow — ✅ Done

- [x] Repo scaffolded: `app/`, `app/core/`, `tests/`, `docs/`, `requirements.txt`, `.env.example`, `.gitignore`, `Dockerfile`, `docker-compose.yml` (content lives in those files now, not duplicated here)
- [x] Personal git identity set per-repo (`daffaarravi@gmail.com`), not the work identity
- [x] GitHub repo created (`daffa-pradana/receipt_digitizer`), scaffold pushed to `main`
- [x] Branch protection on `main`: PR + 1 approval required, enforced for admins too, conversations must resolve, no force-push/delete
- [x] siapahayooo1709 added as collaborator (write access) and accepted the invite
- [x] First PR (#1, `docs: add contributing section`) opened, approved, merged
- [x] `README.md` documents the branch/PR/approve/merge workflow for contributors

## Phase 1: Core pipeline, testable offline (2 to 3 hours) — 🔄 In progress

Build `core/` so it runs on a sample image with no UI and no database.

- [x] `preprocess.py`: `clean(image_bytes) -> numpy array` — decode, resize, grayscale, adaptive threshold
- [x] `ocr.py`: `read(image) -> (full_text, lines_with_conf)` wrapping EasyOCR. Load the `Reader` once at module level via a getter, not per call
- [x] `extract.py`: `extract(full_text) -> {merchant, category, amount, confidence}` using keyword-priority regex + category dictionary from `ARCHITECTURE.md`
- [x] `tests/test_extract.py` with fixed OCR-text strings (no image needed): verifies `Rp 25.000`, `Total Belanja 150.000`, that `Kembali` / change is never picked up as the total, category matching, and the largest-amount fallback when no keyword line is found

**Acceptance:**
- [x] `python -m pytest` passes on the extraction tests (verified locally, no OCR/Docker needed for this part)
- [ ] A quick script prints a sensible amount and category for one real receipt photo — **still pending**, needs EasyOCR/Docker (or a local install) plus an actual receipt photo to run against; `preprocess.py`/`ocr.py` are written but unverified against real images until then

## Phase 2: Database layer (1 hour)

- [ ] `db.py`: `init_schema()`, `insert_transactions(rows)`, `spending_by_category() -> list of (category, total)`
- [ ] `transactions` table created from `ARCHITECTURE.md`'s schema on startup
- [ ] Connection settings read from `config.py`

**Acceptance:** running against the Dockerised Postgres, an insert then a `spending_by_category()` call returns the expected totals.

## Phase 3: Streamlit UI (2 to 3 hours)

`app/main.py` wires it together:

- [ ] Title and a short intro
- [ ] `st.file_uploader(accept_multiple_files=True)`; block more than 5 files
- [ ] On upload, run each file through preprocess → ocr → extract, collect rows into a DataFrame
- [ ] `st.data_editor(df)` so the user can correct merchant, category, amount
- [ ] Save button calling `db.insert_transactions(...)`
- [ ] Query `spending_by_category()` and draw a Plotly pie chart below it
- [ ] Cache the EasyOCR Reader with `@st.cache_resource`

**Acceptance:** upload → edit → save → chart works entirely in the browser.

## Phase 4: Dockerize and full run (1 hour)

- [ ] `docker compose up --build` succeeds (do this well ahead of the demo, the build is large)
- [ ] App reaches Postgres using host `db` (not `localhost`)
- [ ] OCR models are baked in — confirmed by disconnecting wifi and checking OCR still runs

**Acceptance:** a fresh `docker compose up` on a clean checkout brings up a working app.

## Phase 5: Demo prep (30 min)

- [ ] 5 real, varied receipts placed in `tests/sample_receipts/`
- [ ] Full dry run done, noted which receipts read cleanly
- [ ] One-line honest-AI-framing answer ready (OCR is the ML part; extraction is rule based; the editable table handles OCR errors)
- [ ] Fallback plan ready: app already running in a terminal before presenting, plus a screen recording of a successful run as insurance

**Acceptance:** the full flow runs start to finish in under two minutes.

## Phase 6: Deployment (after the demo)

- [ ] Small VPS provisioned, Docker installed, repo cloned, `.env` copied, `docker compose up -d`
- [ ] Only port 8501 published; Postgres stays on the internal Docker network
- [ ] (Optional) custom Flask + JS frontend added in a `web/` folder, reusing `core/` untouched

## Suggested commit rhythm

Small, phase-aligned commits via PR: `chore: scaffold + docker`, `feat: core preprocessing`, `feat: ocr wrapper`, `feat: rule-based extraction + tests`, `feat: postgres layer`, `feat: streamlit ui`, `docs: readme`. Pull after each merged PR so neither of you is ever reviewing a large diff.
