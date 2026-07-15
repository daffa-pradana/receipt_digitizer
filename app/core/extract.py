import re

# Priority order matters: more specific/reliable keywords are checked first,
# so "Total" wins over "Tunai" (cash given) when both appear on a receipt.
TOTAL_KEYWORDS = (
    r"grand\s*total",
    r"total\s*belanja",
    r"total",
    r"tunai",
    r"bayar",
    r"netto",
)

EXCLUDE_PATTERN = re.compile(r"kembali|change", re.IGNORECASE)

AMOUNT_PATTERN = re.compile(
    r"rp\.?\s*(\d{1,3}(?:[.,]\d{3})+)|(\d{1,3}(?:[.,]\d{3})+)",
    re.IGNORECASE,
)

CATEGORIES = {
    "Groceries": ("alfamart", "indomaret", "superindo", "hypermart", "giant"),
    "F&B": ("kopi", "coffee", "resto", "cafe", "kfc", "mcd", "warung"),
    "Transport": ("grab", "gojek", "pertamina", "shell", "spbu", "mrt"),
    "Pharmacy": ("apotek", "kimia farma", "guardian", "watsons"),
}

DEFAULT_CATEGORY = "Uncategorised"


def normalize_amount(raw: str) -> float:
    """Indonesian formatting: dot/comma are thousands separators, e.g. '25.000' -> 25000."""
    return float(raw.replace(".", "").replace(",", ""))


def find_amount(text: str) -> float | None:
    lines = [line for line in text.splitlines() if not EXCLUDE_PATTERN.search(line)]

    for keyword in TOTAL_KEYWORDS:
        for index, line in enumerate(lines):
            if not re.search(keyword, line, re.IGNORECASE):
                continue
            match = AMOUNT_PATTERN.search(line)
            if match:
                return normalize_amount(match.group(1) or match.group(2))
            # OCR frequently detects a label and its amount as separate line
            # boxes (e.g. "TOTAL BELANJA" / "62,100" on their own lines), so
            # fall back to the very next line when the keyword line itself
            # has no digits.
            if index + 1 < len(lines):
                next_match = AMOUNT_PATTERN.search(lines[index + 1])
                if next_match:
                    return normalize_amount(next_match.group(1) or next_match.group(2))

    return _largest_amount(lines)


def _largest_amount(lines: list[str]) -> float | None:
    amounts = [
        normalize_amount(match.group(1) or match.group(2))
        for line in lines
        for match in AMOUNT_PATTERN.finditer(line)
    ]
    return max(amounts) if amounts else None


def _match_known_merchant(lowered_text: str) -> tuple[str, str] | None:
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in lowered_text:
                return category, keyword
    return None


def find_category(text: str) -> str:
    match = _match_known_merchant(text.lower())
    return match[0] if match else DEFAULT_CATEGORY


def find_merchant(text: str) -> str:
    first_line = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            first_line = stripped
            break

    # Receipt headers (store name/logo) are often the worst-OCR'd part of the
    # image. If the first line doesn't already contain a known merchant
    # keyword, prefer that keyword (found anywhere, e.g. a footer contact
    # line) over the garbled first line.
    match = _match_known_merchant(text.lower())
    if match and match[1] not in first_line.lower():
        return match[1].title()

    return first_line


def extract(full_text: str, confidence: float = 0.0) -> dict:
    return {
        "merchant": find_merchant(full_text),
        "category": find_category(full_text),
        "amount": find_amount(full_text),
        "confidence": confidence,
    }
