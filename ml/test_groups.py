import pandas as pd
import re

def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    t = re.sub(r"[^a-z0-9]", "", text.lower())
    return t

df = pd.read_csv("ml/data/processed/products_cleaned.csv")
print("Total rows:", len(df))
df["group_key"] = df.apply(lambda r: f"{clean_text(r['product_name'])}_{clean_text(r['brand'])}", axis=1)
print("Unique group keys:", df["group_key"].nunique())
dup_counts = df["group_key"].value_counts()
print("Top duplicate groups:")
print(dup_counts.head(10))
