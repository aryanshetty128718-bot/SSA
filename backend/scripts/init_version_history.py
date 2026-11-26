import sys
sys.path.append('backend')
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS scoring_version_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version VARCHAR(20) NOT NULL UNIQUE,
            released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    """))
    conn.commit()

    conn.execute(text("""
        INSERT OR IGNORE INTO scoring_version_history (version, released_at, description, is_active)
        VALUES 
        ('1.0.0', '2026-11-20 10:00:00', 'Initial multi-criteria 8-parameter scoring engine with Nutri-Score 2023 integration.', 0),
        ('1.1.0', '2026-11-24 14:00:00', 'Sugar cap implementation (<=39.0 for >30g sugars with natural dried fruit exemption) and beverage-specific sugar weight prioritization (40%).', 1)
    """))
    conn.commit()

    rows = conn.execute(text("SELECT id, version, released_at, description, is_active FROM scoring_version_history")).fetchall()
    print("Scoring Version History:")
    for r in rows:
        print(r)
