import sqlite3

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

# Map non-canonical category slugs / IDs to canonical category IDs
# First get all canonical category IDs:
c.execute("SELECT id, slug FROM categories")
cat_map = {slug: id for id, slug in c.fetchall()}
print("Existing categories:", cat_map)

# Target canonical categories:
# 1. breakfast-cereals: cat_map['breakfast-cereals'] (1)
# 2. chocolates-confectionery: cat_map['chocolates-confectionery'] (7)
# 3. sweet-spreads-nut-butters: cat_map['sweet-spreads-nut-butters'] (18)
# 4. soft-drinks-sodas: cat_map['soft-drinks-sodas'] (2)
# 5. fruit-juices: cat_map['fruit-juices'] (17)
# 6. dairy-plant-drinks: cat_map['dairy-plant-drinks'] (9)
# 7. yoghurts: cat_map['yoghurts'] (15)
# 8. biscuits-cookies: cat_map['biscuits-cookies'] (5)
# 9. breads-bakery: cat_map['breads-bakery'] (10)
# 10. chips-crisps: cat_map['chips-crisps'] (20)
# 11. instant-noodles-pasta: cat_map['instant-noodles-pasta'] (19)

reassignments = [
    # chips
    ("chips-savory-snacks", "chips-crisps"),
    ("chips-crisps-snacks", "chips-crisps"),
    # juices
    ("fruit-juices-smoothies", "fruit-juices"),
    # yoghurts
    ("yoghurts-fermented-dairy", "yoghurts"),
    # chocolates
    ("dark-chocolate-bars", "chocolates-confectionery"),
    ("dark-chocolates", "chocolates-confectionery"),
    # breads
    ("white-breads", "breads-bakery"),
    ("toaste", "breads-bakery"),
    ("breads", "breads-bakery"),
    ("multigrain-sliced-breads", "breads-bakery"),
    # biscuits
    ("crackers", "biscuits-cookies"),
    # sodas
    ("iced-teas", "soft-drinks-sodas"),
    # noodles
    ("instant-noodles-soups", "instant-noodles-pasta"),
]

for src_slug, dest_slug in reassignments:
    src_id = cat_map.get(src_slug)
    dest_id = cat_map.get(dest_slug)
    if src_id and dest_id:
        c.execute("SELECT count(*) FROM products WHERE category_id = ?", (src_id,))
        cnt = c.fetchone()[0]
        if cnt > 0:
            c.execute("UPDATE products SET category_id = ? WHERE category_id = ?", (dest_id, src_id))
            print(f"Reassigned {cnt} products from '{src_slug}' (ID {src_id}) -> '{dest_slug}' (ID {dest_id})")

# Also check if instant-noodles-pasta has products or if instant-noodles-soups was used
c.execute("SELECT count(*) FROM products WHERE category_id = ?", (cat_map.get("instant-noodles-pasta"),))
print("Instant noodles pasta count:", c.fetchone()[0])

conn.commit()

print("\n--- Final Category Distribution ---")
c.execute("""
    SELECT c.id, c.name, c.slug, count(p.id)
    FROM categories c
    LEFT JOIN products p ON c.id = p.category_id
    GROUP BY c.id
    HAVING count(p.id) > 0
    ORDER BY count(p.id) DESC
""")
for row in c.fetchall():
    print(f"  ID {row[0]:2d}: {row[1]:<30} (slug: {row[2]:<25}) -> {row[3]} products")

conn.close()
