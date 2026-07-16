import pandas as pd
import plotly.express as px
import streamlit as st

from app.core import db, ocr, preprocess
from app.core.extract import CATEGORIES, DEFAULT_CATEGORY, extract

MAX_FILES = 5

st.set_page_config(page_title="Receipt Digitizer", page_icon="🧾")


@st.cache_resource
def ensure_schema() -> None:
    db.init_schema()


@st.cache_resource
def get_ocr_reader():
    return ocr.get_reader()


def process_files(files) -> pd.DataFrame:
    get_ocr_reader()  # warm the cached Reader before the loop below

    rows = []
    for uploaded_file in files:
        cleaned = preprocess.clean(uploaded_file.getvalue())
        full_text, lines_with_conf = ocr.read(cleaned)

        confidences = [confidence for _text, confidence in lines_with_conf]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        result = extract(full_text, confidence=avg_confidence)
        rows.append(
            {
                "source_file": uploaded_file.name,
                "merchant": result["merchant"],
                "category": result["category"],
                "amount": result["amount"],
                "confidence": result["confidence"],
                "raw_text": full_text,
            }
        )
    return pd.DataFrame(rows)


def render_pie_chart() -> None:
    st.subheader("Spending by category")
    totals = db.spending_by_category()
    if not totals:
        st.info("No saved transactions yet.")
        return

    totals_df = pd.DataFrame(totals, columns=["category", "total"])
    fig = px.pie(totals_df, names="category", values="total")
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    ensure_schema()

    st.title("Receipt Digitizer")
    st.write(
        "Upload up to 5 receipt photos. OCR (EasyOCR) reads the text - that's "
        "the machine learning part. The total amount and category are then "
        "extracted with rule-based regex and a keyword dictionary, not "
        "machine learning. Review and correct any cell before saving."
    )

    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    files = st.file_uploader(
        "Receipt photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['uploader_key']}",
    )

    if files and len(files) > MAX_FILES:
        st.error(f"Please upload at most {MAX_FILES} files (got {len(files)}).")
        files = []

    if files:
        uploaded_names = [uploaded_file.name for uploaded_file in files]
        if st.session_state.get("uploaded_names") != uploaded_names:
            with st.spinner("Reading receipts..."):
                st.session_state["extracted_df"] = process_files(files)
            st.session_state["uploaded_names"] = uploaded_names

        st.subheader("Review and correct")
        category_options = [*CATEGORIES.keys(), DEFAULT_CATEGORY]
        edited_df = st.data_editor(
            st.session_state["extracted_df"],
            column_order=["source_file", "merchant", "category", "amount", "confidence"],
            column_config={
                "source_file": st.column_config.TextColumn("File", disabled=True),
                "merchant": st.column_config.TextColumn("Merchant"),
                "category": st.column_config.SelectboxColumn(
                    "Category", options=category_options, required=True
                ),
                "amount": st.column_config.NumberColumn("Amount (Rp)", min_value=0, step=1),
                "confidence": st.column_config.NumberColumn(
                    "OCR confidence", disabled=True, format="%.2f"
                ),
            },
            hide_index=True,
            key="editor",
        )

        if st.button("Save"):
            if edited_df["amount"].isna().any():
                st.error("Every row needs an amount before saving - fill in any blank cells.")
            else:
                db.insert_transactions(edited_df.to_dict("records"))
                st.success(f"Saved {len(edited_df)} transaction(s).")
                del st.session_state["extracted_df"]
                del st.session_state["uploaded_names"]
                st.session_state["uploader_key"] += 1
                st.rerun()

    render_pie_chart()


if __name__ == "__main__":
    main()
