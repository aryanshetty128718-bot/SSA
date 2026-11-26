"""
Search Failure Audit Script.
Evaluates barcode search success rate across a benchmark dataset of barcodes.
Classifies all failures into precise causes:
- success
- not_in_off
- in_off_but_rejected (parser rejected: record detailed reason)
- invalid_check_digit
- barcode_format
- timeout/rate_limit
- other
"""

import os
import sys
import time
from typing import Dict, Any, List
from collections import Counter

# Ensure backend root is on path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.db.session import SessionLocal
from app.services.product_service import product_service
from app.core.exceptions import (
    BarcodeValidationError,
    ProductNotFoundError,
    ExternalAPIUnavailableError,
    InsufficientDataError
)
from app.utils.barcode_validator import validate_barcode

def audit_barcode_search(barcodes_file: str = "ml/data/audit_barcodes.txt") -> Dict[str, Any]:
    if not os.path.exists(barcodes_file):
        print(f"Error: Barcodes file {barcodes_file} not found.")
        return {}

    with open(barcodes_file, "r", encoding="utf-8") as f:
        barcodes = [line.strip() for line in f if line.strip()]

    print(f"\n=======================================================")
    print(f"  RUNNING SEARCH FAILURE AUDIT ON {len(barcodes)} BARCODES")
    print(f"=======================================================\n")

    db = SessionLocal()
    results = []
    
    t0 = time.time()
    for idx, raw_barcode in enumerate(barcodes, start=1):
        outcome = {
            "barcode": raw_barcode,
            "status": "pending",
            "cause": None,
            "detail": None,
            "product_name": None
        }

        try:
            # 1. Barcode format / check digit inspection
            is_valid, val_msg = validate_barcode(raw_barcode)
            if not is_valid:
                if "check digit" in val_msg.lower():
                    outcome["status"] = "failed"
                    outcome["cause"] = "invalid_check_digit"
                    outcome["detail"] = val_msg
                else:
                    outcome["status"] = "failed"
                    outcome["cause"] = "barcode_format"
                    outcome["detail"] = val_msg
                results.append(outcome)
                print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> FAIL ({outcome['cause']}): {outcome['detail']}")
                continue

            # 2. Execute standard search flow
            prod = product_service.get_by_barcode(raw_barcode, db)
            outcome["status"] = "success"
            outcome["product_name"] = prod.name
            outcome["source"] = getattr(prod, "source", "unknown")
            print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> SUCCESS: {prod.name[:35]} (source: {outcome['source']})")

        except BarcodeValidationError as bve:
            outcome["status"] = "failed"
            msg = str(bve)
            if "check digit" in msg.lower():
                outcome["cause"] = "invalid_check_digit"
            else:
                outcome["cause"] = "barcode_format"
            outcome["detail"] = msg
            print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> FAIL ({outcome['cause']}): {msg}")

        except ProductNotFoundError as pnfe:
            outcome["status"] = "failed"
            outcome["cause"] = "not_in_off"
            outcome["detail"] = f"Barcode not found in local DB or Open Food Facts API ({pnfe})"
            print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> FAIL (not_in_off)")

        except InsufficientDataError as ide:
            outcome["status"] = "failed"
            outcome["cause"] = "in_off_but_rejected"
            outcome["detail"] = str(ide)
            print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> FAIL (in_off_but_rejected): {ide}")

        except ExternalAPIUnavailableError as eaue:
            outcome["status"] = "failed"
            outcome["cause"] = "timeout/rate_limit"
            outcome["detail"] = str(eaue)
            print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> FAIL (timeout/rate_limit): {eaue}")

        except Exception as ex:
            outcome["status"] = "failed"
            outcome["cause"] = "other"
            outcome["detail"] = str(ex)
            print(f"[{idx:3d}/{len(barcodes)}] {raw_barcode:<16} -> FAIL (other): {ex}")

        results.append(outcome)
        time.sleep(0.05)  # brief polite throttle

    db.close()
    elapsed = time.time() - t0

    # Aggregate Statistics
    total = len(results)
    successes = sum(1 for r in results if r["status"] == "success")
    failures = total - successes
    success_rate = (successes / total) * 100.0 if total > 0 else 0.0

    cause_counts = Counter(r["cause"] for r in results if r["status"] == "failed")

    print(f"\n=======================================================")
    print(f"                AUDIT RESULTS SUMMARY                  ")
    print(f"=======================================================")
    print(f"Total Barcodes Tested:  {total}")
    print(f"Successful Lookups:     {successes} ({success_rate:.1f}%)")
    print(f"Failed Lookups:         {failures} ({100.0 - success_rate:.1f}%)")
    print(f"Elapsed Time:           {elapsed:.2f}s")
    print(f"-------------------------------------------------------")
    print(f"  Failure Breakdown by Cause:")
    print(f"-------------------------------------------------------")
    print(f"  {'Cause':<24} | {'Count':<6} | {'% of Failures':<14}")
    print(f"  {'-'*24}-|-{'-'*6}-|-{'-'*14}")
    for cause, cnt in cause_counts.most_common():
        pct = (cnt / failures) * 100.0 if failures > 0 else 0.0
        print(f"  {cause:<24} | {cnt:<6} | {pct:>5.1f}%")
    print(f"=======================================================\n")

    return {
        "total": total,
        "successes": successes,
        "failures": failures,
        "success_rate": success_rate,
        "causes": dict(cause_counts),
        "results": results
    }

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "ml/data/audit_barcodes.txt"
    audit_barcode_search(filepath)
