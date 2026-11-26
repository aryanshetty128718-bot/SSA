import sqlite3

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

c.execute("""
    SELECT p.barcode, p.name, p.brand, ps.overall_project_score, ps.official_nutri_score_grade, p.category_id, c.name, c.slug
    FROM products p
    JOIN categories c ON p.category_id = c.id
    LEFT JOIN product_scores ps ON p.id = ps.product_id
    WHERE c.name = 'Sweet Spreads & Nut Butters' OR c.slug LIKE '%spread%'
""")
rows = c.fetchall()
print("Products in Sweet Spreads & Nut Butters:")
for r in rows:
    print(r)

conn.close()
