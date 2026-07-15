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
    r"rp\.?\s*(\d[\d.,]*)|(\d{1,3}(?:\.\d{3})+)",
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
        for line in lines:
            if re.search(keyword, line, re.IGNORECASE):
                match = AMOUNT_PATTERN.search(line)
                if match:
                    return normalize_amount(match.group(1) or match.group(2))

    return _largest_amount(lines)


def _largest_amount(lines: list[str]) -> float | None:
    amounts = [
        normalize_amount(match.group(1) or match.group(2))
        for line in lines
        for match in AMOUNT_PATTERN.finditer(line)
    ]
    return max(amounts) if amounts else None


def find_category(text: str) -> str:
    lowered = text.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


def find_merchant(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def extract(full_text: str, confidence: float = 0.0) -> dict:
    return {
        "merchant": find_merchant(full_text),
        "category": find_category(full_text),
        "amount": find_amount(full_text),
        "confidence": confidence,
    }
