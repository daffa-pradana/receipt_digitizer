# Receipt Digitizer (Buku Kas Digital)

Turn up to 5 receipt photos into a categorised expense record with a live spending pie chart. Runs fully local via Docker. OCR is done on-device with EasyOCR, so no cloud API and no API keys.

## What it does

1. Upload up to 5 receipt images (camera or file).
2. OCR reads each receipt (EasyOCR deep learning models).
3. Rules extract the total amount and a spending category.
4. You review and correct the results in an editable table.
5. Save to PostgreSQL and see the pie chart update.

## Requirements

- Docker and Docker Compose.
- The first build is large (it installs PyTorch and bakes the OCR models in). Run it once ahead of time.

## Quickstart

```bash
git clone git@github.com:daffa-pradana/receipt_digitizer.git
cd receipt_digitizer
cp .env.example .env      # adjust the password if you like
make up
```

Open http://localhost:8501

`make` wraps the common Docker commands so you don't need to remember the raw `docker compose` invocations:

```bash
make help       # list all commands
make up         # build (if needed) and start the app + database
make down       # stop everything (keeps saved data)
make logs       # follow the app's logs
make reset-db   # wipe saved transactions, keep the schema
make nuke       # stop everything and delete the database volume (fresh start)
make shell      # open a shell inside the running app container
make psql       # open a psql prompt against the database
make test       # run the extraction unit tests (no Docker needed)
```

No `make`? The plain command is `docker compose up --build`.

To also run pgAdmin for inspecting the database:

```bash
docker compose --profile admin up
# pgAdmin at http://localhost:5050
```

## Contributing

This is a personal project. Set your identity per repo so commits use your personal address, not a work one:

```bash
git config user.name "Your Name"
git config user.email "your-personal@email.com"
```

`main` is protected: no direct pushes, including from admins. To make a change:

```bash
git checkout -b your-feature-name main
# make your changes, commit
git push -u origin your-feature-name
gh pr create --base main   # or open the PR from the GitHub UI
```

- At least one approval (from either reviewer) is required before a PR can merge.
- Any open review conversations must be resolved before merging.
- Force-pushes and deletion of `main` are blocked.

## Project structure

```
app/main.py          Streamlit UI
app/core/            preprocessing, OCR, extraction, database (UI-independent)
tests/               extraction unit tests + sample receipts
docs/                PRD, architecture, action plan
Dockerfile, docker-compose.yml, requirements.txt
```

## Notes

- OCR is the machine learning part. Amount and category extraction are rule based (see `docs/PRD.md`, section 8).
- Amounts assume Indonesian formatting (`Rp 25.000` = 25,000).
- Do not expose PostgreSQL publicly when deploying; keep it on the internal Docker network.

## License

MIT, personal project.
