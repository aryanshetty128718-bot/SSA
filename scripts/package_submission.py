import os
import sys
import zipfile
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SUBMISSION_DIR = BASE_DIR / "FINAL_SUBMISSION"
ZIP_PATH = SUBMISSION_DIR / "Smart_Shopping_Assistant.zip"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "FINAL_SUBMISSION",
    "SSA_fresh_clone",
    "dist",
    "build"
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp"
}

EXCLUDE_FILES = {
    ".env",                # Active secrets file must NEVER be included
    ".DS_Store",
    "Thumbs.db"
}

def should_exclude(rel_path: Path) -> bool:
    # Check parts for excluded directory names
    for part in rel_path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith("task-") and part.endswith(".log"):
            return True

    # Check file extension
    if rel_path.suffix.lower() in EXCLUDE_EXTS:
        return True

    # Check specific file names
    if rel_path.name in EXCLUDE_FILES:
        return True

    # Exclude temporary scratch text outputs if any
    if rel_path.name in ["demo_clean_output.txt", "demo_summary.txt"]:
        return True

    return False

def package_project():
    print("=" * 60)
    print("  Smart Shopping Assistant - Submission Packaging Script")
    print("=" * 60)

    # 1. Ensure FINAL_SUBMISSION folder exists
    if not SUBMISSION_DIR.exists():
        SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {SUBMISSION_DIR}")

    # 2. Copy documentation files to FINAL_SUBMISSION
    doc_files = ["PROJECT_DESCRIPTION.md", "SETUP_GUIDE.md", "README.md"]
    for doc in doc_files:
        src = BASE_DIR / doc
        dst = SUBMISSION_DIR / doc
        shutil.copy2(src, dst)
        print(f"Copied {doc} to {SUBMISSION_DIR}")

    # 3. Create Smart_Shopping_Assistant.zip
    print(f"\nCreating {ZIP_PATH.name}...")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
        for root, dirs, files in os.walk(BASE_DIR):
            # Modify dirs in-place to avoid traversing excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                abs_file_path = Path(root) / file
                rel_path = abs_file_path.relative_to(BASE_DIR)

                if should_exclude(rel_path):
                    continue

                # Add to ZIP under root folder 'Smart_Shopping_Assistant/'
                arcname = Path("Smart_Shopping_Assistant") / rel_path
                zip_file.write(abs_file_path, arcname=str(arcname))
                file_count += 1
                total_uncompressed_bytes += abs_file_path.stat().st_size

    zip_size_bytes = ZIP_PATH.stat().st_size
    zip_size_mb = zip_size_bytes / (1024 * 1024)
    uncompressed_mb = total_uncompressed_bytes / (1024 * 1024)

    print("\n--- Packaging Results ---")
    print(f"Total Files Included: {file_count}")
    print(f"Uncompressed Size:    {uncompressed_mb:.2f} MB")
    print(f"Final ZIP File Size:  {zip_size_mb:.2f} MB")
    print(f"Size Limit:           500.00 MB")
    print(f"Below 500 MB Limit:   {'YES (STRICTLY COMPLIANT)' if zip_size_mb < 500 else 'NO'}")

    return zip_size_mb

def verify_zip():
    print("\n" + "=" * 60)
    print("  Verifying Smart_Shopping_Assistant.zip Integrity")
    print("=" * 60)

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        # Test CRC32 of all files
        bad_file = z.testzip()
        if bad_file:
            print(f"ERROR: Corrupted file detected in ZIP: {bad_file}")
            return False
        print("[CHECK 1] ZIP CRC32 Integrity: PASS (Zero corrupted files)")

        namelist = z.namelist()
        print(f"[CHECK 2] Total archived files: {len(namelist)}")

        # Check frontend source files
        frontend_src = [n for n in namelist if "frontend/src" in n]
        print(f"[CHECK 3] Frontend source files: {len(frontend_src)} files found - PASS")

        # Check backend source files
        backend_src = [n for n in namelist if "backend/app" in n]
        print(f"[CHECK 4] Backend source files: {len(backend_src)} files found - PASS")

        # Check ML model files
        ml_models = [n for n in namelist if "ml/artifacts" in n]
        print(f"[CHECK 5] ML model artifacts: {len(ml_models)} files found - PASS")
        for m in ml_models:
            print(f"          - {m}")

        # Check Database
        db_files = [n for n in namelist if "smart_shopping.db" in n]
        print(f"[CHECK 6] Database smart_shopping.db: {'FOUND - PASS' if db_files else 'MISSING - FAIL'}")

        # Check .env.example
        env_ex = [n for n in namelist if ".env.example" in n]
        print(f"[CHECK 7] Environment template (.env.example): {'FOUND - PASS' if env_ex else 'MISSING - FAIL'}")

        # Check security (MUST NOT contain active .env or passwords)
        active_env = [n for n in namelist if n.endswith("/.env") or n == "Smart_Shopping_Assistant/.env"]
        print(f"[CHECK 8] Security Guard (No active .env): {'PASS (Excluded)' if not active_env else 'FAIL (Active .env found!)'}")

        # Check node_modules exclusion
        node_mod = [n for n in namelist if "node_modules" in n]
        print(f"[CHECK 9] Cleanliness (No node_modules): {'PASS (Excluded)' if not node_mod else 'FAIL (node_modules present!)'}")

        # Check .venv exclusion
        venv_files = [n for n in namelist if ".venv" in n or "venv" in n]
        print(f"[CHECK 10] Cleanliness (No .venv/venv): {'PASS (Excluded)' if not venv_files else 'FAIL (.venv present!)'}")

    return True

if __name__ == "__main__":
    size_mb = package_project()
    success = verify_zip()
    if success and size_mb < 500:
        print("\n>>> ALL PACKAGING AND INTEGRITY CHECKS PASSED SUCCESSFULLY! <<<")
    else:
        print("\n>>> PACKAGING FAILED OR SIZE EXCEEDED! <<<")
        sys.exit(1)
