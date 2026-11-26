import re
from typing import Tuple, List

VALID_BARCODE_LENGTHS = (8, 12, 13, 14)

def clean_raw_barcode(barcode: str) -> str:
    """Strips leading/trailing whitespace, internal spaces, hyphens, and dots."""
    if not barcode:
        return ""
    return re.sub(r"[\s\-\.]+", "", str(barcode).strip())

def calculate_gs1_check_digit(digits: str) -> int:
    """
    Calculate GS1 standard Modulo-10 check digit for an input string of digits.
    Weights alternate 3, 1, 3, 1... moving right to left from the digit immediately
    preceding the check position.
    """
    total = 0
    for i, char in enumerate(reversed(digits)):
        weight = 3 if i % 2 == 0 else 1
        total += int(char) * weight
    remainder = total % 10
    return (10 - remainder) % 10

def validate_barcode(barcode: str, verify_check_digit: bool = True) -> Tuple[bool, str]:
    """
    Validates a product barcode.
    Requirements:
    - Non-empty string
    - Digits only (after cleaning whitespace/hyphens)
    - Standard GS1 length: GTIN-8 (8), UPC-12 (12), EAN-13 (13), ITF-14 (14)
    - Valid GS1 Modulo-10 check digit (if verify_check_digit is True)
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not barcode:
        return False, "Barcode cannot be empty."

    clean_barcode = clean_raw_barcode(barcode)

    if not clean_barcode.isdigit():
        return False, f"Barcode '{barcode}' contains invalid non-numeric characters. Digits only are permitted."

    length = len(clean_barcode)
    if length not in VALID_BARCODE_LENGTHS:
        return False, (
            f"Invalid barcode length ({length} digits). "
            f"Must be one of standard GS1 lengths: 8 (GTIN-8), 12 (UPC-12), 13 (EAN-13), or 14 (ITF-14)."
        )

    if verify_check_digit:
        payload = clean_barcode[:-1]
        expected_check = calculate_gs1_check_digit(payload)
        actual_check = int(clean_barcode[-1])

        if actual_check != expected_check:
            return False, (
                f"Invalid check digit for barcode '{clean_barcode}'. "
                f"Expected check digit is {expected_check}, but got {actual_check}."
            )

    return True, "Valid barcode."

def normalize_barcode(barcode: str) -> str:
    """Returns stripped numeric barcode or raises ValueError if invalid."""
    clean = clean_raw_barcode(barcode)
    is_valid, msg = validate_barcode(clean)
    if not is_valid:
        raise ValueError(msg)
    return clean

def get_barcode_variants(barcode: str) -> List[str]:
    """
    Generates standard GS1 barcode representations for lookup fallback:
    - 12-digit UPC-A <-> 13-digit EAN-13 (leading 0)
    - 14-digit GTIN-14 -> 13-digit EAN-13 (strip packaging indicator digit)
    Deduplicated list preserving canonical primary first.
    """
    clean = clean_raw_barcode(barcode)
    if not clean.isdigit():
        return [clean]

    variants = [clean]

    # UPC-A (12 digits) -> EAN-13 (13 digits with leading zero)
    if len(clean) == 12:
        ean13 = "0" + clean
        is_valid, _ = validate_barcode(ean13)
        if is_valid and ean13 not in variants:
            variants.append(ean13)

    # EAN-13 starting with 0 -> UPC-A (12 digits)
    elif len(clean) == 13 and clean.startswith("0"):
        upc12 = clean[1:]
        is_valid, _ = validate_barcode(upc12)
        if is_valid and upc12 not in variants:
            variants.append(upc12)

    # GTIN-14 -> EAN-13 without indicator digit
    elif len(clean) == 14:
        cand_ean13 = clean[1:]
        # check if cand_ean13 check digit matches
        if len(cand_ean13) == 13:
            payload = cand_ean13[:-1]
            chk = calculate_gs1_check_digit(payload)
            fixed_ean13 = payload + str(chk)
            if fixed_ean13 not in variants:
                variants.append(fixed_ean13)

    return variants
