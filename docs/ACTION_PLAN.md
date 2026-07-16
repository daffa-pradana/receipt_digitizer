# Action Plan & Progress Tracker

This is the shared source of truth for what's done and what's left. Check items off as they land on `main` (i.e. once their PR is merged), so both of you stay in sync without needing a separate status meeting. Update the **Current status** table whenever a phase's state changes.

Status legend: `[x]` done · `(in progress)` next to a phase title means actively being worked · unmarked phases haven't started.

## Current status

Split rationale: Daffa owns everything that needs Docker/WSL/Python fluency to build or debug. siapahayooo1709 owns demo-day legwork, PR review, and small self-contained content contributions (e.g. the category dictionary) that don't need git/terminal at all — see his phases for how.

| Phase | Owner | Status |
|---|---|---|
| 0: Scaffold, git identity, PR workflow | Daffa | ✅ Done |
| 1: Core pipeline (preprocess/OCR/extract) | Daffa | ✅ Done |
| 2: Database layer | Daffa | ✅ Done |
| 3: Streamlit UI | Daffa | ✅ Done |
| Pre-demo accuracy hardening | Daffa | ✅ Done |
| 4: Dockerize and full run | Daffa | ✅ Done |
| 5: Demo prep | siapahayooo1709 | 🔄 In progress |
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

## Phase 1: Core pipeline, testable offline (2 to 3 hours) — ✅ Done

Build `core/` so it runs on a sample image with no UI and no database.

- [x] `preprocess.py`: `clean(image_bytes) -> numpy array` — decode, resize, grayscale, adaptive threshold
- [x] `ocr.py`: `read(image) -> (full_text, lines_with_conf)` wrapping EasyOCR. Load the `Reader` once at module level via a getter, not per call
- [x] `extract.py`: `extract(full_text) -> {merchant, category, amount, confidence}` using keyword-priority regex + category dictionary from `ARCHITECTURE.md`
- [x] `tests/test_extract.py` with fixed OCR-text strings (no image needed): verifies `Rp 25.000`, `Total Belanja 150.000`, that `Kembali` / change is never picked up as the total, category matching, and the largest-amount fallback when no keyword line is found

**Acceptance:**
- [x] `python -m pytest` passes on the extraction tests (verified locally, no OCR/Docker needed for this part)
- [x] A quick script prints a sensible amount and category for one real receipt photo — validated via `docker compose` against two real photos: an Indomaret receipt (merchant, category, and amount all extracted correctly after two bug fixes: keyword+amount split across separate OCR lines, and comma as a thousands separator) and a Cinere-Jagorawi toll receipt (category/merchant correct via the `toll`/`e-toll` keywords, but amount stayed unrecoverable — OCR quality on that one was too poor, an expected case for the human review table to catch, consistent with the PRD's 4-of-5 bar)

## Phase 2: Database layer (1 hour) — ✅ Done

- [x] `db.py`: `init_schema()`, `insert_transactions(rows)`, `spending_by_category() -> list of (category, total)`
- [x] `transactions` table created from `ARCHITECTURE.md`'s schema on startup
- [x] Connection settings read from `config.py`

**Acceptance:** running against the Dockerised Postgres, an insert then a `spending_by_category()` call returns the expected totals — [x] verified: ran `docker compose up -d db`, inserted two rows across different categories twice, and `spending_by_category()` correctly returned accumulated per-category totals both times (confirming `init_schema()` is idempotent). Test rows truncated afterward.

## Phase 3: Streamlit UI (2 to 3 hours) — ✅ Done

`app/main.py` wires it together:

- [x] Title and a short intro (with the honest AI framing: OCR is ML, extraction is rule-based)
- [x] `st.file_uploader(accept_multiple_files=True)`; blocks more than 5 files with an error message
- [x] On upload, run each file through preprocess → ocr → extract, collect rows into a DataFrame (cached in `st.session_state` so re-running the OCR pipeline isn't triggered on every widget interaction, only on a new set of uploaded files)
- [x] `st.data_editor(df)` so the user can correct merchant, category (as a dropdown constrained to the known categories), amount (blocks Save if any row's amount is blank); `raw_text` stays in the underlying data for the DB insert but is hidden from the visible columns
- [x] Save button calling `db.insert_transactions(...)`, then resets the uploader for the next batch
- [x] Query `spending_by_category()` and draw a Plotly pie chart below it
- [x] Cache the EasyOCR Reader with `@st.cache_resource` (wraps `ocr.get_reader()`'s own module-level singleton); schema init is also wrapped in `@st.cache_resource` so it only runs once per process, not on every rerun

**Acceptance:** upload → edit → save → chart works entirely in the browser.
- [x] Verified via `docker compose up`: server starts cleanly with no tracebacks in `docker compose logs app`, and `curl http://localhost:8501/` returns HTTP 200
- [x] Full interactive click-through confirmed manually: uploaded 5 receipts, reviewed/edited the table, saved (data persisted across reloads, confirming it hit Postgres), pie chart updated

**Two real bugs found and fixed during that manual click-through** (not caught by the automated checks above, since those only prove the server *starts*, not that a live browser session can *run the script*):
- `ModuleNotFoundError: No module named 'app'` in production — the running container was serving a **stale image** built before Phase 2/3 existed (we'd only ever tested new code via one-off bind-mounted `docker compose run` commands, never rebuilt the actual image `docker compose up` uses). Once rebuilt, the same root cause as the Phase 1 `check_pipeline.py` bug showed up for real: `streamlit run app/main.py` puts the script's own directory on `sys.path`, not `/app`, so the top-level `app` package was unreachable. Fixed with `ENV PYTHONPATH=/app` in the `Dockerfile`, placed right before the final `COPY` (not right after `WORKDIR`, which was tried first and invalidated the cache for every layer after it, forcing a full torch/EasyOCR re-download).
- A stale healthcheck (`pg_isready -U $POSTGRES_USER` with no `-d` flag, from Phase 0) spams `FATAL: database "receipt" does not exist` in the `db` logs every 5 seconds — harmless (Postgres still reports healthy), but worth knowing it's noise, not a real error, if it comes up again.

## Pre-demo accuracy hardening — ✅ Done

Testing all 5 receipts in `tests/sample_receipts/` against `tests/supposed_result.json` (ground truth) surfaced real gaps — some genuine OCR limitations, some just missing keyword coverage. Fixed the fixable ones:

- [x] `CATEGORIES` expanded: new `Entertainment` category (`xxi`, `cgv`, `cinepolis`, `bioskop`, `m-tix`); `Transport` += `traveloka`, `tiket.com`, `kereta api`, `citilink`, `garuda`, `lion air`, `batik air`; plus more Indonesian F&B/Groceries/Pharmacy brands
- [x] `ocr.read_best()`: runs OCR on both a plain grayscale variant and the adaptive-threshold variant, keeps whichever gives higher mean confidence — binarization can help faded receipts but hurt clean ones, so trying both instead of committing to one beat guessing
- [x] Review-UX: uploaded photos viewable in an expander next to the table; rows with a missing amount or confidence below 0.4 get a `⚠️` flag column plus a summary warning banner

**Result, re-tested against all 5 real receipts after these fixes:**

| Receipt | Merchant | Category | Amount |
|---|---|---|---|
| Indomaret | ✅ exact | ✅ | ✅ exact (62.100) |
| Kopi Tuku | near-miss (OCR dropped one letter: "TUU" vs "TUKU") | ✅ | ✅ exact (113.000) |
| Flight/Traveloka | ✅ exact | ✅ | ✅ exact (1.760.788) — was completely wrong before the grayscale variant fixed it |
| Cinema (m-tix) | reasonable ("Xxi", the chain name) | ✅ | ✅ exact (236.000) |
| Toll road | generic ("Toll" vs "PT Translingkar") | ✅ | unrecoverable — OCR never captured the true digits anywhere in the text (`Rp. 141H11`), a genuine image-quality ceiling, not a regex bug |

4 of 5 fully correct or near-perfect; the one remaining gap is a documented, inherent OCR limitation the editable review table exists to catch — consistent with the PRD's 4-of-5 success bar.

## Phase 4: Dockerize and full run (1 hour) — ✅ Done

- [x] `docker compose up --build` succeeds (rebuilt several times tonight; cache preserved except for the layers that actually changed)
- [x] App reaches Postgres using host `db` (not `localhost`) — confirmed via real saves persisting across reloads
- [x] OCR models are baked in — confirmed with `docker run --network none` (stronger than a wifi-disconnect test, since it guarantees zero network access at the container level): OCR still ran and extracted the Indomaret receipt correctly with no internet

**Acceptance:** a fresh `docker compose up` on a clean checkout brings up a working app. ✅ verified above.

## Phase 5: Demo prep (30 min) — 🔄 In progress (siapahayooo1709)

- [x] 5 real, varied receipts placed in `tests/sample_receipts/` — but 2 of them (cinema, flight) are **app/PDF screenshots**, not physical printed receipts; recommend swapping in physical Indonesian receipts for the actual demo since that's the thesis' own declared scope (see `tests/supposed_result.json` for the current ground truth and `.tmp/enhancement_options.md` for the full reasoning) — **not yet done**
- [x] Full dry run done — see the Phase 3/hardening results table above; 4/5 correct or near-perfect
- [ ] One-line honest-AI-framing answer ready — material exists throughout this doc and the PRD's section 8, but siapahayooo1709 should prepare it in his own words since he's defending it
- [ ] Fallback plan ready: app already running in a terminal before presenting, plus a screen recording of a successful run as insurance — **not yet done**

**Acceptance:** the full flow runs start to finish in under two minutes.

## Phase 6: Deployment (after the demo)

- [ ] Small VPS provisioned, Docker installed, repo cloned, `.env` copied, `docker compose up -d`
- [ ] Only port 8501 published; Postgres stays on the internal Docker network
- [ ] (Optional) custom Flask + JS frontend added in a `web/` folder, reusing `core/` untouched

## Suggested commit rhythm

Small, phase-aligned commits via PR: `chore: scaffold + docker`, `feat: core preprocessing`, `feat: ocr wrapper`, `feat: rule-based extraction + tests`, `feat: postgres layer`, `feat: streamlit ui`, `docs: readme`. Pull after each merged PR so neither of you is ever reviewing a large diff.
