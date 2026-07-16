from app.core.extract import (
    extract,
    find_amount,
    find_category,
    find_merchant,
    normalize_amount,
)


def test_normalize_amount_indonesian_thousands():
    assert normalize_amount("25.000") == 25000.0


def test_finds_amount_with_rp_prefix():
    text = "ALFAMART\nTotal: Rp 25.000\nTunai: Rp 30.000"
    assert find_amount(text) == 25000.0


def test_finds_amount_total_belanja_without_prefix():
    text = "WARUNG MAKAN\nTotal Belanja 150.000\nBayar 150.000"
    assert find_amount(text) == 150000.0


def test_does_not_pick_change_as_total():
    text = "TOKO\nTunai Rp 200.000\nKembali Rp 50.000\nTotal Rp 150.000"
    assert find_amount(text) == 150000.0


def test_falls_back_to_largest_amount_without_keyword():
    text = "RANDOM RECEIPT\n25.000\n10.000"
    assert find_amount(text) == 25000.0


def test_no_amount_found_returns_none():
    assert find_amount("NO NUMBERS HERE") is None


def test_finds_amount_with_comma_thousands_separator():
    # Not every receipt follows the dot-as-thousands convention in practice.
    text = "TOKO\nTotal: 62,100"
    assert find_amount(text) == 62100.0


def test_finds_amount_when_keyword_and_value_are_on_separate_ocr_lines():
    # Reproduces a real Indomaret receipt: EasyOCR frequently detects a
    # label and its amount as separate line boxes, and this one used a
    # comma thousands separator with no "Rp" prefix.
    text = "\n".join(
        [
            "BUKiT RIVARIA SEKTOR 2",
            "TOTAL BELANJH",  # OCR misread of "TOTAL BELANJA"
            "62,100",
            "NoN   TunAi",
            "62,100",
        ]
    )
    assert find_amount(text) == 62100.0


def test_category_matches_known_merchant():
    text = "ALFAMART SUKAJADI\nTotal Rp 25.000"
    assert find_category(text) == "Groceries"


def test_category_defaults_to_uncategorised():
    text = "SOME UNKNOWN SHOP\nTotal Rp 25.000"
    assert find_category(text) == "Uncategorised"


def test_merchant_uses_first_line_when_it_already_names_the_brand():
    text = "KOPI KENANGAN\nTotal Rp 25.000"
    assert find_merchant(text) == "KOPI KENANGAN"


def test_merchant_falls_back_to_known_keyword_when_header_is_garbled():
    # Reproduces the real Indomaret receipt: the store name/logo OCR'd as
    # garbage, but "indomaret" is still readable from a footer contact line.
    text = "\n".join(
        [
            "JL",
            "E_WITRI",
            "SEkTCR2 BlOK",
            "KONTAK@INDOMARET.CO.ID",
        ]
    )
    assert find_merchant(text) == "Indomaret"


def test_category_and_merchant_for_toll_receipt():
    # Reproduces a real, heavily-garbled Cinere-Jagorawi toll receipt: almost
    # nothing OCR'd cleanly, but "TOLL" and "e-Toll" survived intact.
    text = "\n".join(
        [
            "WT: 1 {ANSLINCKAR Kita",
            "JAGOQAMI TOLL",
            "GUL-| e-Toll Handiri",
        ]
    )
    assert find_category(text) == "Transport"
    assert find_merchant(text) == "Toll"


def test_category_and_merchant_for_cinema_receipt():
    # Reproduces a real m-tix (cinema) e-ticket receipt: the app's own name
    # OCR'd as garbage ("Bix"), but "Cinema XXI" survived as "GoncmaXXI".
    text = "\n".join(
        [
            "Bix",
            "Detail pesenanmudimtix)",
            "GoncmaXXI",
            "Total payment)",
            "Rp236.000,00",
        ]
    )
    assert find_category(text) == "Entertainment"
    assert find_merchant(text) == "Xxi"


def test_category_and_merchant_for_traveloka_receipt():
    # Reproduces a real Traveloka flight e-receipt: badly garbled overall,
    # but "traveloka" survived clean enough to substring-match.
    text = "\n".join(
        [
            "6.25 @@ #",
            "(traveloka",
            "TOTAL",
            "1.n30",
        ]
    )
    assert find_category(text) == "Transport"
    assert find_merchant(text) == "Traveloka"


def test_extract_returns_full_result():
    text = "KOPI KENANGAN\nTotal Rp 25.000"
    result = extract(text, confidence=0.87)
    assert result == {
        "merchant": "KOPI KENANGAN",
        "category": "F&B",
        "amount": 25000.0,
        "confidence": 0.87,
    }
