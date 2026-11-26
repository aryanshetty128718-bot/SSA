import pytest
from app.utils.barcode_validator import validate_barcode, calculate_gs1_check_digit, normalize_barcode

def test_valid_barcodes():
    # 8-digit EAN-8
    assert validate_barcode("96385074")[0] is True
    
    # 12-digit UPC-A
    assert validate_barcode("012345678905")[0] is True
    
    # 13-digit EAN-13 (Ferrero Nutella real barcode)
    assert validate_barcode("3017620422003")[0] is True
    
    # 14-digit ITF-14
    assert validate_barcode("10012345678902")[0] is True

def test_invalid_length():
    valid, msg = validate_barcode("1234567")  # 7 digits
    assert valid is False
    assert "Invalid barcode length" in msg

    valid, msg = validate_barcode("123456789")  # 9 digits
    assert valid is False
    assert "Invalid barcode length" in msg

    valid, msg = validate_barcode("123456789012345")  # 15 digits
    assert valid is False
    assert "Invalid barcode length" in msg

def test_non_numeric():
    valid, msg = validate_barcode("301762042200A")
    assert valid is False
    assert "non-numeric" in msg

    valid, msg = validate_barcode("301-762-0422")
    assert valid is False
    assert "non-numeric" in msg

def test_invalid_check_digit():
    # 3017620422003 with check digit replaced by 4
    valid, msg = validate_barcode("3017620422004")
    assert valid is False
    assert "Expected check digit is 3, but got 4" in msg

def test_normalize_barcode():
    assert normalize_barcode("  3017620422003  ") == "3017620422003"
    with pytest.raises(ValueError):
        normalize_barcode("invalid_code")
