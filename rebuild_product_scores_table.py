import sqlite3

def make_points_nullable():
    con = sqlite3.connect("smart_shopping.db")
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("""
    CREATE TABLE product_scores_new (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        product_id VARCHAR(36) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        overall_project_score FLOAT NOT NULL,
        project_health_band VARCHAR(30) NOT NULL,
        official_nutri_score_grade VARCHAR(20) NOT NULL,
        official_nutri_score_points INTEGER,
        confidence_score FLOAT NOT NULL,
        sub_scores_json TEXT NOT NULL,
        pros_json TEXT NOT NULL,
        cons_json TEXT NOT NULL,
        scoring_engine_version VARCHAR(20) NOT NULL,
        calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    INSERT INTO product_scores_new 
    SELECT id, product_id, overall_project_score, project_health_band, 
           official_nutri_score_grade, official_nutri_score_points, 
           confidence_score, sub_scores_json, pros_json, cons_json, 
           scoring_engine_version, calculated_at 
    FROM product_scores;
    """)
    cur.execute("DROP TABLE product_scores;")
    cur.execute("ALTER TABLE product_scores_new RENAME TO product_scores;")
    cur.execute("CREATE INDEX ix_product_scores_id ON product_scores (id);")
    cur.execute("CREATE INDEX ix_product_scores_product_id ON product_scores (product_id);")
    cur.execute("PRAGMA foreign_keys = ON;")
    con.commit()
    con.close()
    print("product_scores table successfully rebuilt with nullable official_nutri_score_points and VARCHAR(20) grade!")

if __name__ == "__main__":
    make_points_nullable()
