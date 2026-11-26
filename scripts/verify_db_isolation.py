import hashlib
import subprocess
import sys
import os

def get_db_hash(filepath="smart_shopping.db"):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    db_path = "smart_shopping.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist.")
        sys.exit(1)

    hash_before = get_db_hash(db_path)
    print("=" * 70)
    print("DATABASE ISOLATION & INTEGRITY VERIFICATION")
    print("=" * 70)
    print(f"Target Database:       {db_path}")
    print(f"SHA-256 (BEFORE SUITE): {hash_before}")
    print("\nRunning complete backend test suite under isolated test runner...")
    
    # Run pytest
    res = subprocess.run([sys.executable, "-m", "pytest", "backend/tests/"], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)

    hash_after = get_db_hash(db_path)
    print(f"SHA-256 (AFTER SUITE):  {hash_after}")
    
    if hash_before == hash_after:
        print("\n" + "=" * 70)
        print("PASS: Checksums match exactly! smart_shopping.db was NEVER modified.")
        print("=" * 70)
        if res.returncode != 0:
            print("Warning: Some tests failed, but DB was completely untouched.")
            sys.exit(res.returncode)
        else:
            print(f"All tests passed ({res.returncode} exit code) with 100% zero DB mutations.")
            sys.exit(0)
    else:
        print("\n" + "!" * 70)
        print("FAIL: Checksums differ! Database was altered during tests.")
        print("!" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
