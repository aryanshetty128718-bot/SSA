import sqlite3

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

c.execute("""
    SELECT p.barcode, p.name, p.brand, c.name, c.slug
    FROM products p
    JOIN categories c ON p.category_id = c.id
    WHERE (
        LOWER(p.name) LIKE '%peanut butter%' OR
        LOWER(p.name) LIKE '%pâte à tartiner%' OR
        LOWER(p.name) LIKE '%hazelnut spread%' OR
        LOWER(p.name) LIKE '%almond butter%' OR
        LOWER(p.name) LIKE '%nut butter%' OR
        LOWER(p.name) LIKE '%jam%' OR
        LOWER(p.name) LIKE '%confiture%' OR
        LOWER(p.name) LIKE '%honey%' OR
        LOWER(p.name) LIKE '%miel%'
    ) AND c.slug != 'sweet-spreads-nut-butters'
""")
mis = c.fetchall()
print(f"Found {len(mis)} spread products categorized elsewhere:")
for m in mis[:20]:
    print("  ", m)

conn.close()
