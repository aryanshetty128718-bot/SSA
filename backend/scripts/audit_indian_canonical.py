import sqlite3

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

query = """
SELECT c.name AS category_name, c.slug, count(DISTINCT p.id) AS indian_products_count
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN product_category_tags pct ON p.id = pct.product_id
WHERE p.source = 'openfoodfacts'
  AND (
    p.barcode LIKE '890%'
    OR p.origin_country LIKE '%india%'
    OR pct.tag LIKE '%en:india%'
  )
GROUP BY c.id
ORDER BY indian_products_count DESC;
"""

c.execute(query)
rows = c.fetchall()

print("--- CANONICAL INDIAN OPENFOODFACTS PRODUCT COVERAGE (DISTINCT PRODUCTS) ---")
total_indian = 0
for r in rows:
    print(f"  {r[0]:<30} (slug: {r[1]:<25}): {r[2]} products")
    total_indian += r[2]

print(f"\nTotal DISTINCT real Indian OFF products in DB: {total_indian}")

# Also check how many have GS1 prefix 890 specifically
query_890 = """
SELECT c.name, count(DISTINCT p.id)
FROM products p
JOIN categories c ON p.category_id = c.id
WHERE p.source = 'openfoodfacts' AND p.barcode LIKE '890%'
GROUP BY c.id
ORDER BY count(DISTINCT p.id) DESC;
"""
c.execute(query_890)
print("\n--- Indian Products with GS1 890 Barcode Prefix ---")
tot_890 = 0
for r in c.fetchall():
    print(f"  {r[0]:<30}: {r[1]} products")
    tot_890 += r[1]
print(f"Total 890-prefix OFF products: {tot_890}")

conn.close()
