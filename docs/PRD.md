# PRD: AI Receipt Digitizer (Buku Kas Digital)

**Status:** Draft v1 for MVP / thesis demo
**Author:** (brother, thesis owner)
**Reviewer / co-dev:** Daffa
**Target demo:** Wednesday (lecturer)
**Repo owner identity:** daffaarravi@gmail.com

---

## 1. Problem

Manual bookkeeping from paper receipts is slow and error prone. People take photos of receipts and never transcribe them, so they lose track of where money goes. We want a tool that turns a stack of receipt photos into a structured, categorised expense record with almost no typing.

## 2. Goals

- Let a user upload up to 5 receipt photos in one session (camera or file).
- Automatically read each receipt and extract two things: the total amount and a spending category.
- Show the extracted data in an editable table so the user can fix OCR mistakes before saving.
- Persist confirmed records to a database.
- Show a live pie chart of spending by category from the saved data.
- Run fully local for the demo, with zero paid services, and be reproducible on any machine via Docker.

## 3. Non-goals (MVP)

- No user accounts / auth. Single-user demo.
- No line-item level parsing (we capture the total per receipt, not every product line).
- No trained ML classifier. Category assignment is rule based for the MVP (see honest AI framing below).
- No mobile app. Responsive web is enough.
- No multi-currency. Indonesian Rupiah only.

## 4. Target user

The user's own brother / a student or individual who wants a quick personal expense tracker. Non technical. Uses a phone camera and a laptop browser.

## 5. Functional requirements

### FR1: Batch upload
- Accept 1 to 5 image files (jpg, jpeg, png) per session.
- Reject more than 5 with a clear message.
- Files held in memory only; nothing written to disk before the user saves.

### FR2: Preprocessing
- Resize large phone photos to a working width (target ~800 to 1000 px).
- Convert to grayscale.
- Apply adaptive thresholding to raise text contrast on uneven lighting.

### FR3: OCR extraction
- Run OCR on each preprocessed image and return recognised text with confidence.
- This is the AI / deep learning component (see section 8).

### FR4: Amount + category extraction
- From the OCR text, find the total spend using keyword anchored regex (Total, Grand Total, Total Belanja, Tunai, Bayar) and Indonesian number format (dot as thousands separator, e.g. `Rp 25.000`).
- Assign a category by matching merchant keywords against a dictionary (e.g. Alfamart / Indomaret to Groceries, Kopi / Resto to F&B, Grab / Gojek to Transport). Default to Uncategorised when no match.

### FR5: Interactive validation
- Show all extracted rows (filename, merchant guess, category, amount, OCR confidence) in an editable table.
- The user can correct any cell, especially the amount and category.
- Nothing is saved until the user clicks Save.

### FR6: Persistence
- On Save, insert the confirmed rows into PostgreSQL.
- Store: id, source filename, merchant, category, amount, raw OCR text (for audit), created_at.

### FR7: Dashboard
- Query saved data (SUM grouped by category) and render a pie chart of spending allocation.
- Chart updates after each save.

## 6. Non-functional requirements

- **Local first:** the whole app runs offline on a laptop for the demo. OCR models are baked into the Docker image so no internet is needed on demo day.
- **Free:** every runtime dependency is open source and free. The only optional cost is a small VPS after the demo.
- **Reproducible:** `docker compose up` starts the app and database with no manual setup beyond copying `.env`.
- **Portable:** the brother can clone the repo and run the exact same stack.
- **Acceptable latency:** OCR on CPU may take a few seconds per image. Acceptable for 5 images in a demo.

## 7. Success metrics (demo)

- Upload 5 real receipts, get a total extracted for at least 4 of them without manual retype.
- Correct any misread cell in the table and save successfully.
- Pie chart reflects the saved totals correctly.
- Fresh clone on the brother's machine runs with one command.

## 8. Honest AI framing (important for the defense)

Be precise with the lecturer about what is and is not machine learning. This protects the thesis under questioning.

- **Machine learning / deep learning:** the OCR stage. Text detection uses a CRAFT-style detector and recognition uses a CRNN (ResNet + LSTM) model, both via EasyOCR. This is the genuine AI contribution.
- **Classical computer vision:** the OpenCV preprocessing (resize, grayscale, adaptive threshold). Not learned, but standard and defensible.
- **Rule based, not ML:** amount extraction (regex) and category assignment (keyword dictionary). Present these honestly as a rule based layer. A trained category classifier is listed as future work, not claimed as done.
- **Human in the loop:** the editable validation table is a deliberate design response to imperfect OCR, not a workaround to hide. Frame it as a strength.

## 9. Risks and assumptions

- OCR accuracy on crumpled thermal receipts is imperfect. Mitigation: preprocessing plus the human validation step.
- EasyOCR pulls PyTorch, so the first Docker build is large and slow. Mitigation: build the image the night before, models baked in.
- Photos taken at an angle reduce accuracy. Out of scope for MVP; note deskew as future work.

## 10. Scope split

| Phase | Contents |
|---|---|
| MVP (by Wed) | FR1 to FR7 with Streamlit UI, PostgreSQL, Docker, rule based extraction |
| Post-demo | Deploy to a small VPS, optional custom Flask + JS frontend, deskew, trained classifier, line-item parsing |
