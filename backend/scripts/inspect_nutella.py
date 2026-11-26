import sqlite3
import json

conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in c.fetchall()])

c.execute('SELECT * FROM products WHERE barcode = ?', ('3017620422003',))
prod = c.fetchone()
c.execute('PRAGMA table_info(products)')
cols = [col[1] for col in c.fetchall()]
print('Nutella product:')
for col, val in zip(cols, prod):
    print(f'  {col}: {val}')

c.execute("SELECT * FROM categories WHERE id = ?", (prod[cols.index('category_id')],))
cat = c.fetchone()
print('Nutella category row:', cat)

c.execute('SELECT * FROM nutrition_facts WHERE product_barcode = ?', ('3017620422003',))
nutr = c.fetchone()
c.execute('PRAGMA table_info(nutrition_facts)')
nutr_cols = [col[1] for col in c.fetchall()]
print('Nutella nutrition row:')
if nutr:
    for col, val in zip(nutr_cols, nutr):
        print(f'  {col}: {val}')
else:
    print('  NO NUTRITION ROW FOUND!')

c.execute('SELECT * FROM ingredients WHERE product_barcode = ?', ('3017620422003',))
ings = c.fetchall()
print(f'Ingredients count: {len(ings)}')
for i in ings[:5]:
    print('  ', i)

c.execute('SELECT * FROM product_scores WHERE product_barcode = ?', ('3017620422003',))
sc = c.fetchone()
c.execute('PRAGMA table_info(product_scores)')
sc_cols = [col[1] for col in c.fetchall()]
print('Product score row:')
if sc:
    for col, val in zip(sc_cols, sc):
        print(f'  {col}: {val}')

conn.close()
