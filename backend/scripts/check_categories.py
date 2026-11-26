import sqlite3

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

c.execute("SELECT id, name, slug, product_type FROM categories ORDER BY id")
cats = c.fetchall()
print("All categories in DB:")
for cat in cats:
    c.execute("SELECT count(*) FROM products WHERE category_id = ?", (cat[0],))
    cnt = c.fetchone()[0]
    print(f"  ID {cat[0]:2d}: {cat[1]:<30} (slug: {cat[2]:<25}, type: {cat[3]}) -> {cnt} prods")

conn.close()
