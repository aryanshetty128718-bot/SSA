import re

with open("C:/Users/Admin/.gemini/antigravity/brain/a2d49800-f258-4eb9-a8c8-0df4df44a059/.system_generated/steps/1663/output.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Filter out SQL log lines
lines = [l for l in text.splitlines() if "INFO     | sqlalchemy.engine" not in l and "Loaded ML" not in l]
clean_text = "\n".join(lines)

with open("C:/Users/Admin/.gemini/antigravity/scratch/SSA/demo_clean_output.txt", "w", encoding="utf-8") as f:
    f.write(clean_text)

print("Wrote clean demo output to demo_clean_output.txt")
