"""
Migration and Backfill Script for Level 2 Product Types.
Creates product_types table, adds product_type_id to products table,
populates all 45 product types from backend/app/core/taxonomy.py,
and backfills every product in the database.
"""

import os
import sys
import sqlite3
from typing import Dict, Any

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.core.taxonomy import PRODUCT_TYPES, PRODUCT_TYPE_BY_ID, map_product_to_type

def migrate_and_backfill(db_path: str = "smart_shopping.db"):
    print(f"\n=======================================================")
    print(f"  RUNNING PRODUCT TYPES TAXONOMY MIGRATION & BACKFILL  ")
    print(f"=======================================================\n")
    print(f"Target Database: {db_path}")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Ensure product_types table exists
    c.execute("""
    CREATE TABLE IF NOT EXISTS product_types (
        id INTEGER PRIMARY KEY,
        slug VARCHAR(64) UNIQUE NOT NULL,
        name VARCHAR(128) NOT NULL,
        category_id INTEGER NOT NULL,
        category_slug VARCHAR(64) NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    )
    """)

    # 2. Check if product_type_id column exists on products
    cols = [col[1] for col in c.execute("PRAGMA table_info(products)").fetchall()]
    if "product_type_id" not in cols:
        print("Adding column 'product_type_id' to products table...")
        c.execute("ALTER TABLE products ADD COLUMN product_type_id INTEGER REFERENCES product_types(id) ON DELETE SET NULL")
        c.execute("CREATE INDEX IF NOT EXISTS ix_products_product_type_id ON products (product_type_id)")
    else:
        print("Column 'product_type_id' already exists in products table.")

    # 3. Populate product_types
    # First map category_slug to category_id
    cat_rows = c.execute("SELECT id, slug FROM categories").fetchall()
    cat_slug_to_id = {row[1]: row[0] for row in cat_rows}

    # Fallback to category 1 if slug not found
    fallback_cat_id = cat_rows[0][0] if cat_rows else 1

    print(f"Seeding {len(PRODUCT_TYPES)} product types into product_types table...")
    for pt in PRODUCT_TYPES:
        c_id = cat_slug_to_id.get(pt["category_slug"], fallback_cat_id)
        c.execute("""
        INSERT INTO product_types (id, slug, name, category_id, category_slug)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            slug = excluded.slug,
            name = excluded.name,
            category_id = excluded.category_id,
            category_slug = excluded.category_slug
        """, (pt["id"], pt["slug"], pt["name"], c_id, pt["category_slug"]))

    conn.commit()

    # 4. Backfill all products with Level 2 product_type_id
    print("Backfilling existing products with deterministic Level 2 taxonomy mapping...")
    products = c.execute("""
    SELECT p.id, p.name, p.brand, c.slug
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    """).fetchall()

    updated = 0
    for pid, pname, pbrand, cslug in products:
        # Fetch tags
        tags = [row[0] for row in c.execute("SELECT tag FROM product_category_tags WHERE product_id = ?", (pid,)).fetchall()]
        pt_match = map_product_to_type(
            product_name=pname or "",
            brand=pbrand or "",
            category_tags=tags,
            project_category_slug=cslug
        )
        c.execute("UPDATE products SET product_type_id = ? WHERE id = ?", (pt_match["id"], pid))
        updated += 1

    conn.commit()
    print(f"Successfully backfilled {updated} products.\n")

    # 5. Product counts per product type report
    counts = c.execute("""
    SELECT pt.id, pt.name, pt.category_slug, count(p.id) as product_count
    FROM product_types pt
    LEFT JOIN products p ON pt.id = p.product_type_id
    GROUP BY pt.id
    ORDER BY pt.category_slug, product_count DESC
    """).fetchall()

    print(f"-------------------------------------------------------------------------------------")
    print(f"  {'ID':<3} | {'Product Type Name':<32} | {'Category Slug':<24} | {'Count':<6}")
    print(f"  {'-'*3}-|-{'-'*32}-|-{'-'*24}-|-{'-'*6}")
    total_assigned = 0
    empty_types = 0
    for row in counts:
        ptid, ptname, catslug, cnt = row
        total_assigned += cnt
        if cnt == 0:
            empty_types += 1
        print(f"  {ptid:<3} | {ptname:<32} | {catslug:<24} | {cnt:<6}")
    print(f"-------------------------------------------------------------------------------------")
    print(f"Total Products Assigned: {total_assigned} across {len(counts)} Product Types")
    print(f"Empty Product Types:     {empty_types}")
    print(f"=====================================================================================\n")

    conn.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "smart_shopping.db"
    migrate_and_backfill(db_file)