import re

with open("C:/Users/Admin/.gemini/antigravity/scratch/SSA/demo_clean_output.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Keep lines that do not look like SQL queries
sql_keywords = ["SELECT", "FROM", "WHERE", "LIMIT", "OFFSET", "INSERT INTO", "ORDER BY", "JOIN"]
filtered = []
for line in text.splitlines():
    s = line.strip()
    if any(s.startswith(k) for k in sql_keywords):
        continue
    if s.startswith("?") or s.startswith("(") or s.startswith(")") or s.startswith("AND") or s.startswith("OR"):
        continue
    if s:
        filtered.append(line)

summary_text = "\n".join(filtered)
print(summary_text)

with open("C:/Users/Admin/.gemini/antigravity/scratch/SSA/demo_summary.txt", "w", encoding="utf-8") as f:
    f.write(summary_text)
