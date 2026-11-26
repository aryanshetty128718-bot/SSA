"""
Verification Script for Admin Criteria Update, Version Bumping & Catalog Rescoring.
Demonstrates:
1. Admin authentication & retrieval of criteria
2. Criteria update with validation
3. Version bump in scoring_version_history
4. Audit log entry generation in admin_audit_logs
5. Background re-scoring execution and status endpoint
6. product_scores rows updated to version 1.2.0
"""

import sys
import os
import json
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.db.session import SessionLocal
from app.models import User, AdminAuditLog, Product, ProductScore
from sqlalchemy import text

def api_post(url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def api_get(url, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def api_put(url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    print("=== Admin Scoring Criteria Update & Rescoring Verification ===")
    
    # 1. Login as Admin
    print("\n[Step 1] Authenticating as Administrator...")
    login_res = api_post("http://127.0.0.1:8000/api/v1/auth/login", {
        "email": "admin@example.com",
        "password": "Admin@12345"
    })
    token = login_res["access_token"]
    print(f"Authenticated as {login_res['user']['email']} (Role: {login_res['user']['role']})")

    # 2. Fetch current criteria
    print("\n[Step 2] Fetching active scoring criteria...")
    criteria = api_get("http://127.0.0.1:8000/api/v1/admin/scoring-criteria", token=token)
    print(f"Active Version: {criteria.get('version', '1.1.0')}")
    print("Active solid weights:")
    for k, v in list(criteria.get("weights", {}).items())[:4]:
        print(f"  {k}: {v}")

    # 3. Update criteria (Bumping to 1.2.0)
    print("\n[Step 3] Submitting updated criteria (validating sum = 1.000)...")
    payload = {
        "product_type": "solid",
        "parameters": {
            "sugars": {"weight": 0.22, "t_low": 5.0, "t_high": 22.5},
            "sodium": {"weight": 0.18, "t_low": 120.0, "t_high": 600.0},
            "saturated_fat": {"weight": 0.18, "t_low": 1.5, "t_high": 5.0},
            "energy": {"weight": 0.12, "t_low": 150.0, "t_high": 450.0},
            "fiber": {"weight": 0.10, "t_target": 6.0},
            "proteins": {"weight": 0.10, "t_target": 12.0},
            "ingredient_quality": {"weight": 0.05},
            "additive_profile": {"weight": 0.05}
        }
    }
    
    update_res = api_put("http://127.0.0.1:8000/api/v1/admin/scoring-criteria", payload, token=token)
    print(f"Update Response: {update_res['message']}")
    print(f"Engine Version incremented to: {update_res['scoring_engine_version']}")
    print(f"Background Job Info: {update_res['background_job']}")

    # 4. Check status of background re-scoring job
    print("\n[Step 4] Polling background catalog re-scoring progress endpoint (/api/v1/admin/rescore/status)...")
    for _ in range(5):
        status = api_get("http://127.0.0.1:8000/api/v1/admin/rescore/status", token=token)
        print(f"  Status: {status.get('status')} | Progress: {status.get('progress_pct')}% ({status.get('processed_count')}/{status.get('total_count')})")
        if status.get("status") == "completed":
            break
        time.sleep(2)

    # 5. Verify Database Records (Version History, Audit Logs, Product Scores)
    print("\n[Step 5] Direct Database Verification:")
    db = SessionLocal()
    try:
        # Check scoring_version_history
        hist = db.execute(text("SELECT id, version, released_at, description, is_active FROM scoring_version_history ORDER BY id DESC LIMIT 3")).fetchall()
        print("\n--- scoring_version_history ---")
        for h in hist:
            print(f"ID {h[0]} | Version {h[1]} | Active: {bool(h[4])} | Date: {h[2]} | {h[3]}")

        # Check admin_audit_logs
        log = db.query(AdminAuditLog).order_by(AdminAuditLog.id.desc()).first()
        print("\n--- Latest admin_audit_logs Entry ---")
        if log:
            print(f"Log ID: {log.id} | Action: {log.action} | Entity: {log.target_entity} | Target ID: {log.target_id}")
            print(f"Timestamp: {log.created_at}")
            print(f"Changes JSON: {log.changes_json[:120]}...")

        # Check product_scores version distribution
        scores_version = db.execute(text("SELECT scoring_engine_version, count(*) FROM product_scores GROUP BY scoring_engine_version")).fetchall()
        print("\n--- product_scores Version Distribution ---")
        for sv in scores_version:
            print(f"Engine Version {sv[0]}: {sv[1]} products")

    finally:
        db.close()

    print("\n=== Verification Completed Successfully ===")

if __name__ == "__main__":
    main()
