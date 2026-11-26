import sqlite3

c1 = sqlite3.connect('smart_shopping.demo.db')
c2 = sqlite3.connect('smart_shopping.db')

tables = [r[0] for r in c1.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Checking {len(tables)} tables...")

found_diff = False
for t in tables:
    if t.startswith('sqlite_'):
        continue
    r1 = c1.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    r2 = c2.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    if r1 != r2:
        print(f"DIFFERENCE in count for {t}: demo={r1} vs live={r2}")
        found_diff = True
    else:
        rows1 = c1.execute(f"SELECT * FROM {t}").fetchall()
        rows2 = c2.execute(f"SELECT * FROM {t}").fetchall()
        if rows1 != rows2:
            print(f"CONTENT DIFFERENCE in {t} ({len(rows1)} rows)!")
            found_diff = True

if not found_diff:
    print("NO TABLE DIFFERENCES! Data rows are 100% identical.")
    # Check SQLite header bytes
    with open('smart_shopping.demo.db', 'rb') as f1, open('smart_shopping.db', 'rb') as f2:
        b1 = f1.read(100)
        b2 = f2.read(100)
        print("Header comparison (first 100 bytes):", "MATCH" if b1 == b2 else "DIFFER")
        # Find where byte difference starts
        f1.seek(0)
        f2.seek(0)
        all1 = f1.read()
        all2 = f2.read()
        print(f"Size demo: {len(all1)}, Size live: {len(all2)}")
        for idx in range(min(len(all1), len(all2))):
            if all1[idx] != all2[idx]:
                print(f"First differing byte at offset {idx}: demo={all1[idx]} vs live={all2[idx]}")
                break
