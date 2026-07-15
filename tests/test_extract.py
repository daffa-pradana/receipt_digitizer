from app.core.extract import extract, find_amount, find_category, normalize_amount


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


def test_category_matches_known_merchant():
    text = "ALFAMART SUKAJADI\nTotal Rp 25.000"
    assert find_category(text) == "Groceries"


def test_category_defaults_to_uncategorised():
    text = "SOME UNKNOWN SHOP\nTotal Rp 25.000"
    assert find_category(text) == "Uncategorised"


def test_extract_returns_full_result():
    text = "KOPI KENANGAN\nTotal Rp 25.000"
    result = extract(text, confidence=0.87)
    assert result == {
        "merchant": "KOPI KENANGAN",
        "category": "F&B",
        "amount": 25000.0,
        "confidence": 0.87,
    }
