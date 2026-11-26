import sqlite3

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

c.execute("SELECT count(*) FROM products")
total_prods = c.fetchone()[0]

c.execute("""
    SELECT count(DISTINCT p.id)
    FROM products p
    LEFT JOIN nutritional_information n ON p.id = n.product_id
    WHERE n.id IS NULL
""")
prods_without_nutr = c.fetchone()[0]

c.execute("""
    SELECT count(DISTINCT p.id)
    FROM products p
    LEFT JOIN product_ingredients pi ON p.id = pi.product_id
    WHERE pi.id IS NULL
""")
prods_without_ings = c.fetchone()[0]

print(f"Total products: {total_prods}")
print(f"Products without nutritional_information: {prods_without_nutr}")
print(f"Products without ingredients in product_ingredients: {prods_without_ings}")

# Check source breakdown for missing ingredients and nutrition
c.execute("""
    SELECT p.source, count(p.id)
    FROM products p
    LEFT JOIN product_ingredients pi ON p.id = pi.product_id
    WHERE pi.id IS NULL
    GROUP BY p.source
""")
print("Missing ingredients by source:", c.fetchall())

c.execute("""
    SELECT p.source, count(p.id)
    FROM products p
    LEFT JOIN nutritional_information n ON p.id = n.product_id
    WHERE n.id IS NULL
    GROUP BY p.source
""")
print("Missing nutrition by source:", c.fetchall())

# Check alternatives count distribution across all products
print("\nChecking alternatives across categories...")
c.execute("""
    SELECT c.name, count(p.id)
    FROM categories c
    LEFT JOIN products p ON c.id = p.category_id
    GROUP BY c.id
    ORDER BY count(p.id) ASC
""")
print("Products per category:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} products")

conn.close()
