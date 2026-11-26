"""
Two-Level Taxonomy Architecture (Version 1.0.0).
Level 1: 11 Project Categories (+ other)
Level 2: 50 Specific Culinary Product Types with OFF tag mapping, keyword heuristics,
and documented Tier 2 relatedness maps for category-coherent recommendations.
"""

from typing import Dict, List, Any, Optional

TAXONOMY_VERSION = "1.0.0"

# Product Types Definition: 50 Granular Product Types across 11 Project Categories
PRODUCT_TYPES: List[Dict[str, Any]] = [
    # 1. Instant Noodles & Pasta
    {
        "id": 1,
        "slug": "pasta",
        "name": "Dried Pasta",
        "category_slug": "instant-noodles-pasta",
        "product_type": "solid",
        "tags": ["en:pastas", "en:dry-pasta", "en:durum-wheat-pasta", "en:spaghetti", "en:penne", "en:macaroni", "en:fusilli"],
        "keywords": ["pasta", "spaghetti", "penne", "fusilli", "macaroni", "rigate", "linguine", "tagliatelle", "lasagna", "farfalle"],
        "related": ["instant-noodles", "cereal-grains"]
    },
    {
        "id": 2,
        "slug": "instant-noodles",
        "name": "Instant Noodles & Ramen",
        "category_slug": "instant-noodles-pasta",
        "product_type": "solid",
        "tags": ["en:instant-noodles", "en:ramen", "en:asian-noodles", "en:instant-noodle-soups"],
        "keywords": ["instant noodle", "ramen", "maggi", "cup noodles", "soba", "udon", "hakka noodle", "chow mein"],
        "related": ["pasta"]
    },

    # 2. Sweet Spreads & Nut Butters
    {
        "id": 3,
        "slug": "peanut-butter",
        "name": "Peanut Butter",
        "category_slug": "sweet-spreads-nut-butters",
        "product_type": "solid",
        "tags": ["en:peanut-butters", "en:peanut-butter", "en:peanut-spreads"],
        "keywords": ["peanut butter", "beurre de cacahuètes", "beurre de cacahuete", "cacahuète", "peanut paste"],
        "related": ["almond-nut-butter", "hazelnut-chocolate-spread"]
    },
    {
        "id": 4,
        "slug": "almond-nut-butter",
        "name": "Almond & Seed Butters",
        "category_slug": "sweet-spreads-nut-butters",
        "product_type": "solid",
        "tags": ["en:almond-butters", "en:nut-butters", "en:seed-butters"],
        "keywords": ["almond butter", "cashew butter", "tahini", "sesame butter", "sunflower butter"],
        "related": ["peanut-butter", "hazelnut-chocolate-spread"]
    },
    {
        "id": 5,
        "slug": "hazelnut-chocolate-spread",
        "name": "Chocolate & Hazelnut Spreads",
        "category_slug": "sweet-spreads-nut-butters",
        "product_type": "solid",
        "tags": ["en:chocolate-spreads", "en:hazelnut-spreads", "en:cocoa-and-hazelnuts-spreads", "en:pates-a-tartiner-aux-noisettes-et-au-cacao"],
        "keywords": ["nutella", "hazelnut spread", "chocolate spread", "cocoa spread", "tartiner au chocolat", "pâte à tartiner"],
        "related": ["peanut-butter", "almond-nut-butter", "fruit-jam"]
    },
    {
        "id": 6,
        "slug": "fruit-jam",
        "name": "Fruit Jams & Preserves",
        "category_slug": "sweet-spreads-nut-butters",
        "product_type": "solid",
        "tags": ["en:jams", "en:fruit-jams", "en:marmalades", "en:fruit-preserves", "en:confitures", "en:spreads"],
        "keywords": ["jam", "marmalade", "confiture", "fruit spread", "preserves", "jelly", "strawberry jam", "apricot", "raspberry", "confiture"],
        "related": ["honey", "hazelnut-chocolate-spread"]
    },
    {
        "id": 7,
        "slug": "honey",
        "name": "Honey & Sweet Syrups",
        "category_slug": "sweet-spreads-nut-butters",
        "product_type": "solid",
        "tags": ["en:honeys", "en:honey", "en:maple-syrups", "en:agave-syrups"],
        "keywords": ["honey", "miel", "maple syrup", "agave", "pancake syrup"],
        "related": ["fruit-jam"]
    },

    # 3. Breakfast Cereals
    {
        "id": 8,
        "slug": "oats-porridge",
        "name": "Oats & Porridge",
        "category_slug": "breakfast-cereals",
        "product_type": "solid",
        "tags": ["en:oats", "en:rolled-oats", "en:porridge", "en:oatmeals", "en:flocons-d-avoine"],
        "keywords": ["oats", "rolled oats", "porridge", "oatmeal", "quaker oats", "masala oats", "avoine"],
        "related": ["muesli-granola", "corn-flakes"]
    },
    {
        "id": 9,
        "slug": "muesli-granola",
        "name": "Muesli & Granola",
        "category_slug": "breakfast-cereals",
        "product_type": "solid",
        "tags": ["en:mueslis", "en:granolas", "en:mueslis-with-fruits", "en:crunchy-mueslis"],
        "keywords": ["muesli", "granola", "crunchy muesli", "cereal cluster"],
        "related": ["oats-porridge", "corn-flakes", "cereal-flakes"]
    },
    {
        "id": 10,
        "slug": "corn-flakes",
        "name": "Corn Flakes",
        "category_slug": "breakfast-cereals",
        "product_type": "solid",
        "tags": ["en:corn-flakes", "en:flaked-cereals"],
        "keywords": ["corn flakes", "cornflakes", "kellogg's corn flakes"],
        "related": ["cereal-flakes", "muesli-granola", "oats-porridge"]
    },
    {
        "id": 11,
        "slug": "cereal-flakes",
        "name": "Multigrain & Bran Flakes",
        "category_slug": "breakfast-cereals",
        "product_type": "solid",
        "tags": ["en:wheat-flakes", "en:bran-flakes", "en:multigrain-cereals"],
        "keywords": ["wheat flakes", "bran flakes", "all-bran", "special k", "multigrain flakes"],
        "related": ["corn-flakes", "muesli-granola", "oats-porridge"]
    },
    {
        "id": 12,
        "slug": "children-cereals",
        "name": "Sweetened & Extruded Cereals",
        "category_slug": "breakfast-cereals",
        "product_type": "solid",
        "tags": ["en:chocolate-cereals", "en:extruded-cereals", "en:puffed-cereals"],
        "keywords": ["chocos", "froot loops", "cheerios", "coco pops", "frosties", "puffs", "krispies"],
        "related": ["corn-flakes", "muesli-granola"]
    },

    # 4. Soft Drinks & Sodas
    {
        "id": 13,
        "slug": "cola",
        "name": "Cola Drinks",
        "category_slug": "soft-drinks-sodas",
        "product_type": "beverage",
        "tags": ["en:colas", "en:sodas", "en:cola-drinks"],
        "keywords": ["coca-cola", "pepsi", "cola", "thums up", "diet coke", "coke zero", "pepsi black"],
        "related": ["flavoured-soda", "sparkling-water"]
    },
    {
        "id": 14,
        "slug": "flavoured-soda",
        "name": "Flavoured Carbonated Sodas",
        "category_slug": "soft-drinks-sodas",
        "product_type": "beverage",
        "tags": ["en:carbonated-drinks", "en:lemonades", "en:orange-sodas", "en:lemon-lime-sodas"],
        "keywords": ["sprite", "fanta", "limca", "mirinda", "mountain dew", "7up", "ginger ale", "tonic water", "carbonated"],
        "related": ["cola", "sparkling-water", "iced-tea"]
    },
    {
        "id": 15,
        "slug": "sparkling-water",
        "name": "Sparkling Water & Seltzer",
        "category_slug": "soft-drinks-sodas",
        "product_type": "beverage",
        "tags": ["en:carbonated-waters", "en:sparkling-waters", "en:flavored-sparkling-waters"],
        "keywords": ["sparkling water", "club soda", "perrier", "san pellegrino", "seltzer", "eau gazeuse"],
        "related": ["flavoured-soda", "cola"]
    },
    {
        "id": 16,
        "slug": "energy-sports-drink",
        "name": "Energy & Sports Drinks",
        "category_slug": "soft-drinks-sodas",
        "product_type": "beverage",
        "tags": ["en:energy-drinks", "en:sports-drinks", "en:isotonic-drinks"],
        "keywords": ["red bull", "monster", "sting", "gatorade", "powerade", "energy drink", "isotonic"],
        "related": ["flavoured-soda", "cola"]
    },
    {
        "id": 17,
        "slug": "iced-tea",
        "name": "Iced Tea & Ready Tea",
        "category_slug": "soft-drinks-sodas",
        "product_type": "beverage",
        "tags": ["en:iced-teas", "en:teas-and-herbal-teas"],
        "keywords": ["iced tea", "nestea", "lipton ice tea", "fuze tea", "the glace"],
        "related": ["flavoured-soda", "sparkling-water"]
    },

    # 5. Fruit Juices
    {
        "id": 18,
        "slug": "pure-fruit-juice",
        "name": "100% Pure Fruit Juice",
        "category_slug": "fruit-juices",
        "product_type": "beverage",
        "tags": ["en:fruit-juices", "en:pure-fruit-juices", "en:squeezed-juices", "en:jus-de-fruits"],
        "keywords": ["100% juice", "pure juice", "pure fruit", "orange juice", "apple juice", "jus d'orange", "jus de pomme"],
        "related": ["fruit-nectar-drink", "smoothie"]
    },
    {
        "id": 19,
        "slug": "fruit-nectar-drink",
        "name": "Fruit Nectars & Drinks",
        "category_slug": "fruit-juices",
        "product_type": "beverage",
        "tags": ["en:fruit-nectars", "en:fruit-drinks", "en:sweetened-fruit-drinks"],
        "keywords": ["nectar", "fruit drink", "maaza", "frooti", "slice", "real fruit power", "tropicana drink"],
        "related": ["pure-fruit-juice", "smoothie"]
    },
    {
        "id": 20,
        "slug": "smoothie",
        "name": "Fruit & Vegetable Smoothies",
        "category_slug": "fruit-juices",
        "product_type": "beverage",
        "tags": ["en:smoothies", "en:fruit-smoothies"],
        "keywords": ["smoothie", "fruit puree", "innocent smoothie", "naked juice"],
        "related": ["pure-fruit-juice", "fruit-nectar-drink"]
    },

    # 6. Dairy & Plant Drinks
    {
        "id": 21,
        "slug": "cows-milk",
        "name": "Fresh & UHT Cow's Milk",
        "category_slug": "dairy-plant-drinks",
        "product_type": "beverage",
        "tags": ["en:milks", "en:whole-milks", "en:semi-skimmed-milks", "en:skimmed-milks", "en:uht-milks"],
        "keywords": ["milk", "lait", "amul milk", "toned milk", "cow milk", "full cream milk", "skimmed milk"],
        "related": ["plant-based-milk", "flavoured-milk"]
    },
    {
        "id": 22,
        "slug": "plant-based-milk",
        "name": "Plant-Based Milk Alternatives",
        "category_slug": "dairy-plant-drinks",
        "product_type": "beverage",
        "tags": ["en:plant-milks", "en:soya-milks", "en:almond-milks", "en:oat-milks", "en:coconut-milks"],
        "keywords": ["almond milk", "soy milk", "soya milk", "oat milk", "coconut milk", "plant drink", "alpro"],
        "related": ["cows-milk", "flavoured-milk"]
    },
    {
        "id": 23,
        "slug": "flavoured-milk",
        "name": "Flavoured Milk & Milkshakes",
        "category_slug": "dairy-plant-drinks",
        "product_type": "beverage",
        "tags": ["en:flavoured-milks", "en:chocolate-milks", "en:milkshakes"],
        "keywords": ["chocolate milk", "strawberry milk", "milkshake", "amul kool", "cavins milkshake", "horlicks", "bournvita"],
        "related": ["cows-milk", "plant-based-milk"]
    },

    # 7. Yoghurts
    {
        "id": 24,
        "slug": "plain-yoghurt",
        "name": "Plain Yoghurt & Dahi",
        "category_slug": "yoghurts",
        "product_type": "solid",
        "tags": ["en:yogurts", "en:plain-yogurts", "en:greek-yogurts", "en:dahi", "en:curd"],
        "keywords": ["yoghurt", "yogurt", "yaourt nature", "dahi", "curd", "plain curd", "greek yogurt"],
        "related": ["flavoured-yoghurt", "drinking-yoghurt"]
    },
    {
        "id": 25,
        "slug": "flavoured-yoghurt",
        "name": "Flavoured & Fruit Yoghurts",
        "category_slug": "yoghurts",
        "product_type": "solid",
        "tags": ["en:flavored-yogurts", "en:fruit-yogurts"],
        "keywords": ["fruit yogurt", "flavoured yogurt", "strawberry yogurt", "danone", "epigamia"],
        "related": ["plain-yoghurt", "drinking-yoghurt"]
    },
    {
        "id": 26,
        "slug": "drinking-yoghurt",
        "name": "Drinking Yoghurt & Buttermilk",
        "category_slug": "yoghurts",
        "product_type": "beverage",
        "tags": ["en:drinking-yogurts", "en:buttermilks", "en:chaas", "en:lassi"],
        "keywords": ["drinking yogurt", "chaas", "buttermilk", "lassi", "actimel", "yakult"],
        "related": ["plain-yoghurt", "flavoured-yoghurt"]
    },

    # 8. Biscuits & Cookies
    {
        "id": 27,
        "slug": "plain-biscuits",
        "name": "Plain & Tea Biscuits",
        "category_slug": "biscuits-cookies",
        "product_type": "solid",
        "tags": ["en:biscuits", "en:tea-biscuits", "en:rich-tea-biscuits", "en:marie-biscuits"],
        "keywords": ["marie gold", "parle-g", "glucose biscuit", "rich tea", "digestive", "arrowroot", "petit beurre"],
        "related": ["cookies", "cream-biscuits", "crackers-savory-biscuits"]
    },
    {
        "id": 28,
        "slug": "cookies",
        "name": "Cookies & Shortbread",
        "category_slug": "biscuits-cookies",
        "product_type": "solid",
        "tags": ["en:cookies", "en:chocolate-chip-cookies", "en:shortbreads"],
        "keywords": ["cookie", "cookies", "chocochip", "good day", "hide & seek", "butter cookie", "shortbread"],
        "related": ["plain-biscuits", "cream-biscuits", "wafers"]
    },
    {
        "id": 29,
        "slug": "cream-biscuits",
        "name": "Cream & Sandwich Biscuits",
        "category_slug": "biscuits-cookies",
        "product_type": "solid",
        "tags": ["en:sandwich-cookies", "en:filled-biscuits", "en:cream-crackers"],
        "keywords": ["oreo", "bourbon", "cream biscuit", "dark fantasy", "sandwich cookie", "biscuit fourre"],
        "related": ["cookies", "plain-biscuits", "wafers"]
    },
    {
        "id": 30,
        "slug": "wafers",
        "name": "Wafers",
        "category_slug": "biscuits-cookies",
        "product_type": "solid",
        "tags": ["en:wafers", "en:chocolate-wafers"],
        "keywords": ["wafer", "wafers", "kitkat", "loacker", "munch"],
        "related": ["cookies", "cream-biscuits"]
    },
    {
        "id": 31,
        "slug": "crackers-savory-biscuits",
        "name": "Crackers & Savoury Biscuits",
        "category_slug": "biscuits-cookies",
        "product_type": "solid",
        "tags": ["en:crackers", "en:savory-crackers", "en:salted-biscuits"],
        "keywords": ["cracker", "crackers", "monaco", "50-50", "salt biscuits", "tuc", "ritz"],
        "related": ["plain-biscuits", "potato-chips"]
    },

    # 9. Breads & Bakery
    {
        "id": 32,
        "slug": "sliced-bread",
        "name": "Sliced Sandwich Bread",
        "category_slug": "breads-bakery",
        "product_type": "solid",
        "tags": ["en:breads", "en:sliced-breads", "en:white-breads", "en:whole-wheat-breads", "en:brown-breads"],
        "keywords": ["bread", "sliced bread", "white bread", "brown bread", "whole wheat bread", "sandwich bread", "pain de mie"],
        "related": ["artisan-bread", "rolls-buns"]
    },
    {
        "id": 33,
        "slug": "artisan-bread",
        "name": "Artisan & Crusty Bread",
        "category_slug": "breads-bakery",
        "product_type": "solid",
        "tags": ["en:baguettes", "en:sourdough-breads", "en:rye-breads"],
        "keywords": ["baguette", "sourdough", "ciabatta", "focaccia", "rye bread", "pain au levain"],
        "related": ["sliced-bread", "rolls-buns"]
    },
    {
        "id": 34,
        "slug": "rolls-buns",
        "name": "Buns, Rolls & Pav",
        "category_slug": "breads-bakery",
        "product_type": "solid",
        "tags": ["en:buns", "en:rolls", "en:burger-buns"],
        "keywords": ["bun", "burger bun", "pav", "bread roll", "brioche"],
        "related": ["sliced-bread", "artisan-bread"]
    },
    {
        "id": 35,
        "slug": "cakes-muffins",
        "name": "Cakes, Muffins & Pastries",
        "category_slug": "breads-bakery",
        "product_type": "solid",
        "tags": ["en:cakes", "en:muffins", "en:pastries", "en:sponge-cakes"],
        "keywords": ["cake", "muffin", "cupcake", "brownie", "croissant", "pastry", "gateau"],
        "related": ["rolls-buns", "cookies"]
    },

    # 10. Chips & Crisps
    {
        "id": 36,
        "slug": "potato-chips",
        "name": "Potato Chips & Crisps",
        "category_slug": "chips-crisps",
        "product_type": "solid",
        "tags": ["en:chips", "en:potato-chips", "en:crisps", "en:potato-crisps", "en:chips-de-pommes-de-terre"],
        "keywords": ["potato chips", "lays", "pringles", "crisps", "chips", "salted chips", "creme & onion"],
        "related": ["tortilla-nacho-chips", "extruded-snacks"]
    },
    {
        "id": 37,
        "slug": "tortilla-nacho-chips",
        "name": "Tortilla & Corn Nacho Chips",
        "category_slug": "chips-crisps",
        "product_type": "solid",
        "tags": ["en:tortilla-chips", "en:corn-chips", "en:nachos"],
        "keywords": ["tortilla", "nacho", "doritos", "corn chips", "tostitos"],
        "related": ["potato-chips", "extruded-snacks"]
    },
    {
        "id": 38,
        "slug": "extruded-snacks",
        "name": "Extruded & Puffed Snacks",
        "category_slug": "chips-crisps",
        "product_type": "solid",
        "tags": ["en:puffed-snacks", "en:extruded-snacks"],
        "keywords": ["kurkure", "cheetos", "puffcorn", "puffed snacks", "rings", "corn puffs"],
        "related": ["potato-chips", "tortilla-nacho-chips", "roasted-nuts-seeds"]
    },
    {
        "id": 39,
        "slug": "roasted-nuts-seeds",
        "name": "Roasted Nuts & Seeds",
        "category_slug": "chips-crisps",
        "product_type": "solid",
        "tags": ["en:nuts", "en:roasted-nuts", "en:peanuts", "en:almonds", "en:cashews"],
        "keywords": ["roasted peanut", "almonds", "cashews", "pistachio", "walnuts", "mixed nuts", "trail mix"],
        "related": ["potato-chips", "extruded-snacks"]
    },

    # 11. Chocolates & Confectionery
    {
        "id": 40,
        "slug": "dark-chocolate",
        "name": "Dark Chocolate",
        "category_slug": "chocolates-confectionery",
        "product_type": "solid",
        "tags": ["en:dark-chocolates", "en:chocolats-noirs"],
        "keywords": ["dark chocolate", "70%", "85%", "noir", "cacao pur", "bournville"],
        "related": ["milk-chocolate", "chocolate-bars"]
    },
    {
        "id": 41,
        "slug": "milk-chocolate",
        "name": "Milk & White Chocolate",
        "category_slug": "chocolates-confectionery",
        "product_type": "solid",
        "tags": ["en:milk-chocolates", "en:white-chocolates"],
        "keywords": ["dairy milk", "milk chocolate", "white chocolate", "galaxy", "milka"],
        "related": ["dark-chocolate", "chocolate-bars"]
    },
    {
        "id": 42,
        "slug": "chocolate-bars",
        "name": "Filled Chocolate Bars",
        "category_slug": "chocolates-confectionery",
        "product_type": "solid",
        "tags": ["en:chocolate-bars", "en:candy-bars"],
        "keywords": ["snickers", "mars", "bounty", "twix", "5 star", "bar one", "perk"],
        "related": ["dark-chocolate", "milk-chocolate"]
    },

    # 12. Other Staple Foods
    {
        "id": 43,
        "slug": "cereal-grains",
        "name": "Rice & Whole Grains",
        "category_slug": "other",
        "product_type": "solid",
        "tags": ["en:rices", "en:basmati-rices", "en:quinoas", "en:couscous"],
        "keywords": ["rice", "basmati", "quinoa", "couscous", "brown rice", "jasmine rice"],
        "related": ["pasta"]
    },
    {
        "id": 44,
        "slug": "pulses-legumes",
        "name": "Lentils, Dhal & Pulses",
        "category_slug": "other",
        "product_type": "solid",
        "tags": ["en:legumes", "en:lentils", "en:chickpeas", "en:beans"],
        "keywords": ["dal", "dhal", "lentil", "chickpea", "rajma", "moong", "toor dal", "urad dal"],
        "related": ["cereal-grains"]
    },
    {
        "id": 45,
        "slug": "sauces-condiments",
        "name": "Sauces & Condiments",
        "category_slug": "other",
        "product_type": "solid",
        "tags": ["en:sauces", "en:condiments", "en:ketchups", "en:mayonnaises"],
        "keywords": ["ketchup", "sauce", "mayonnaise", "mustard", "chutney", "soya sauce"],
        "related": []
    }
]

# Quick lookup indices
PRODUCT_TYPE_BY_SLUG: Dict[str, Dict[str, Any]] = {pt["slug"]: pt for pt in PRODUCT_TYPES}
PRODUCT_TYPE_BY_ID: Dict[int, Dict[str, Any]] = {pt["id"]: pt for pt in PRODUCT_TYPES}

def map_product_to_type(
    product_name: str,
    brand: Optional[str] = None,
    category_tags: Optional[List[str]] = None,
    project_category_slug: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deterministically maps a product to its Level 2 culinary product type.
    Order of precedence:
    1. Direct match on Open Food Facts category tags
    2. Heuristic keyword search in product title + brand
    3. Fallback to default representative type for the project category
    """
    clean_name = (product_name or "").lower()
    clean_brand = (brand or "").lower()
    combined_text = f"{clean_name} {clean_brand}".lower()
    tags_clean = [t.lower() for t in (category_tags or [])]

    # 1. Open Food Facts tag matches (Exact and high precision)
    for pt in PRODUCT_TYPES:
        for t in pt["tags"]:
            if any(t in ct for ct in tags_clean):
                return pt

    # 2. Text keyword matching
    for pt in PRODUCT_TYPES:
        if project_category_slug and pt["category_slug"] != project_category_slug and project_category_slug != "other":
            continue
        for kw in pt["keywords"]:
            if kw in combined_text:
                return pt

    # 3. Category fallback
    cat_fallbacks = {
        "instant-noodles-pasta": "pasta",
        "sweet-spreads-nut-butters": "peanut-butter",
        "breakfast-cereals": "oats-porridge",
        "soft-drinks-sodas": "flavoured-soda",
        "fruit-juices": "pure-fruit-juice",
        "dairy-plant-drinks": "cows-milk",
        "yoghurts": "plain-yoghurt",
        "biscuits-cookies": "plain-biscuits",
        "breads-bakery": "sliced-bread",
        "chips-crisps": "potato-chips",
        "chocolates-confectionery": "milk-chocolate",
        "other": "cereal-grains"
    }

    target_slug = cat_fallbacks.get(project_category_slug or "", "cereal-grains")
    return PRODUCT_TYPE_BY_SLUG.get(target_slug, PRODUCT_TYPES[0])