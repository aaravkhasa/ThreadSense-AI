"""
ThreadSense AI — Standalone Retail Dataset Generator
Brand: JAK Threads / UrbanVogue / Custom Fashion Brands

CORRECTED VERSION — see notes below.
The version this was based on had two default-parameter mismatches that meant
re-running it fresh would NOT reproduce the dataset actually used in this
project. Both are fixed here; generation logic itself is untouched.

Fix 1: snapshot_date default was 2026-09-01. The dataset actually used to
       build this project's features was generated against 2026-08-25.
       (Confirmed by regenerating with both dates and diffing cell-by-cell
       against jak_threads_raw_data.xlsx — 2026-08-25 matches exactly,
       2026-09-01 does not.)
Fix 2: the __main__ block called brand_name="JAK Threads", which produces
       product names like "JAK Threads Graphic T-Shirts - ...". The actual
       file has "JAK Graphic T-Shirts - ..." (no "Threads"), so the original
       run used brand_name="JAK". Product_ID prefixes are unaffected either
       way (both truncate to "JAK"), only Product_Name text changes.
"""

import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def generate_fashion_dataset(
    brand_name: str = "JAK",                              # <-- fixed (was "JAK Threads")
    n_samples: int = 1200,
    random_state: int = 42,
    snapshot_date: datetime = datetime(2026, 8, 25),       # <-- fixed (was 2026, 9, 1)
    output_dir: str = "./data"
) -> pd.DataFrame:
    """
    Generates a realistic fashion retail dataset incorporating genuine retail dynamics:
    - 3 Operational Cohorts: Fast Movers (35%), Steady Sellers (40%), Slow Movers/Dead Stock (25%)
    - Multi-period sales consistency (7D <= 30D <= 60D <= 90D <= Total Sold)
    - Realistic markup pricing and gross margins (45% - 70%)
    - Omnichannel distribution across digital, social, and offline channels.
    """
    np.random.seed(random_state)
    
    # Category Taxonomy & Cost Structure
    catalog_taxonomy = {
        "Topwear": {
            "subcategories": ["T-Shirts", "Hoodies", "Graphic Polos", "Oversized Shirts"],
            "styles": ["Oversized", "Boxy", "Graphic", "Vintage", "Minimalist", "Acid Wash"],
            "cost_range": (350.0, 750.0),
            "markup_range": (2.2, 3.2),
        },
        "Bottomwear": {
            "subcategories": ["Cargo Pants", "Denim", "Parachute Pants", "Sweat Shorts"],
            "styles": ["Baggy", "Relaxed Fit", "Straight", "Cargo Multi-Pocket", "Distressed"],
            "cost_range": (600.0, 1200.0),
            "markup_range": (2.0, 2.8),
        },
        "Outerwear": {
            "subcategories": ["Varsity Jackets", "Bombers", "Windbreakers", "Zip Hoodies"],
            "styles": ["Vintage Leather-Sleeve", "Minimalist", "Oversized Street", "Colorblocked"],
            "cost_range": (1100.0, 2200.0),
            "markup_range": (1.9, 2.6),
        },
        "Accessories": {
            "subcategories": ["Caps", "Tote Bags", "Socks 3-Pack", "Beanies"],
            "styles": ["Embroidered", "Distressed Vintage", "Canvas Heavy", "Ribbed"],
            "cost_range": (180.0, 450.0),
            "markup_range": (2.3, 3.5),
        }
    }
    
    colors = [
        "Pitch Black", "Off White", "Sage Green", "Charcoal Grey", 
        "Cobalt Blue", "Terracotta", "Vintage Olive", "Washed Crimson", "Earth Brown"
    ]
    sizes = ["S", "M", "L", "XL", "XXL"]
    channels = ["Website", "Instagram DM", "Offline Store", "Marketplace"]
    channel_weights = [0.45, 0.25, 0.15, 0.15]
    
    locations = ["Mumbai Central", "Delhi NCR", "Bengaluru Hub", "Online Warehouse"]
    location_weights = [0.25, 0.25, 0.20, 0.30]
    
    seasons = ["SS26", "FW25", "All-Season"]
    season_weights = [0.50, 0.25, 0.25]
    
    categories = list(catalog_taxonomy.keys())
    cat_weights = [0.45, 0.30, 0.15, 0.10]
    
    records = []
    
    for i in range(1, n_samples + 1):
        prefix = brand_name.replace(" ", "")[:3].upper()
        sku_id = f"{prefix}-{i:04d}"
        
        category = np.random.choice(categories, p=cat_weights)
        cat_info = catalog_taxonomy[category]
        subcategory = np.random.choice(cat_info["subcategories"])
        style = np.random.choice(cat_info["styles"])
        color = np.random.choice(colors)
        size = "Free Size" if category == "Accessories" and subcategory in ["Tote Bags", "Beanies"] else np.random.choice(sizes)
        
        product_name = f"{brand_name} {style} {subcategory} - {color}"
        
        # Financials
        cost_price = round(np.random.uniform(*cat_info["cost_range"]), 2)
        markup = np.random.uniform(*cat_info["markup_range"])
        selling_price = round((cost_price * markup) / 10.0) * 10 - 1.0  # Ends in 99/49
        
        # Operational Cohorts
        cohort_type = np.random.choice(["fast", "normal", "slow"], p=[0.35, 0.40, 0.25])
        
        if cohort_type == "fast":
            age_days = np.random.randint(10, 90)
            initial_stock = np.random.randint(60, 200)
            daily_v = np.random.uniform(1.2, 4.0)
            
            sold_7 = min(initial_stock, int(daily_v * 7 * np.random.uniform(0.9, 1.4)))
            sold_30 = min(initial_stock, max(sold_7, int(daily_v * min(age_days, 30) * np.random.uniform(0.85, 1.15))))
            sold_60 = min(initial_stock, max(sold_30, int(daily_v * min(age_days, 60) * np.random.uniform(0.80, 1.10))))
            sold_90 = min(initial_stock, max(sold_60, int(daily_v * min(age_days, 90) * np.random.uniform(0.75, 1.05))))
            total_sold = min(initial_stock, max(sold_90, int(daily_v * age_days)))
            
            current_stock = max(0, initial_stock - total_sold)
            days_since_last_sale = np.random.randint(0, 4)
            prev_discount = 0.0 if np.random.rand() > 0.15 else 0.10
            
        elif cohort_type == "normal":
            age_days = np.random.randint(25, 140)
            initial_stock = np.random.randint(40, 150)
            daily_v = np.random.uniform(0.4, 1.1)
            
            sold_7 = min(initial_stock, int(daily_v * 7 * np.random.uniform(0.7, 1.2)))
            sold_30 = min(initial_stock, max(sold_7, int(daily_v * min(age_days, 30) * np.random.uniform(0.75, 1.10))))
            sold_60 = min(initial_stock, max(sold_30, int(daily_v * min(age_days, 60) * np.random.uniform(0.70, 1.05))))
            sold_90 = min(initial_stock, max(sold_60, int(daily_v * min(age_days, 90) * np.random.uniform(0.70, 1.00))))
            total_sold = min(initial_stock, max(sold_90, int(daily_v * age_days * 0.85)))
            
            current_stock = max(5, initial_stock - total_sold)
            days_since_last_sale = np.random.randint(2, 14)
            prev_discount = np.random.choice([0.0, 0.10, 0.15], p=[0.6, 0.3, 0.1])
            
        else:  # Slow-moving
            age_days = np.random.randint(50, 180)
            initial_stock = np.random.randint(50, 180)
            daily_v = np.random.uniform(0.02, 0.25)
            
            sold_7 = min(initial_stock, np.random.choice([0, 0, 0, 1, 2]))
            sold_30 = min(initial_stock, max(sold_7, int(daily_v * min(age_days, 30) * np.random.uniform(0.3, 0.8))))
            sold_60 = min(initial_stock, max(sold_30, int(daily_v * min(age_days, 60) * np.random.uniform(0.5, 0.9))))
            sold_90 = min(initial_stock, max(sold_60, int(daily_v * min(age_days, 90) * np.random.uniform(0.6, 1.0))))
            total_sold = min(initial_stock, max(sold_90, int(sold_90 * 1.1)))
            
            current_stock = max(15, initial_stock - total_sold)
            days_since_last_sale = np.random.randint(18, min(age_days, 75))
            prev_discount = np.random.choice([0.0, 0.10, 0.20], p=[0.3, 0.4, 0.3])
            
        launch_date = (snapshot_date - timedelta(days=age_days)).strftime("%Y-%m-%d")
        last_sale_date = (snapshot_date - timedelta(days=days_since_last_sale)).strftime("%Y-%m-%d")
        
        channel = np.random.choice(channels, p=channel_weights)
        location = np.random.choice(locations, p=location_weights)
        season = np.random.choice(seasons, p=season_weights)
        
        records.append({
            "Product_ID": sku_id,
            "Product_Name": product_name,
            "Category": category,
            "Subcategory": subcategory,
            "Style": style,
            "Color": color,
            "Size": size,
            "Cost_Price": cost_price,
            "Selling_Price": selling_price,
            "Current_Stock": int(current_stock),
            "Launch_Date": launch_date,
            "Last_Sale_Date": last_sale_date,
            "Units_Sold_7_Days": int(sold_7),
            "Units_Sold_30_Days": int(sold_30),
            "Units_Sold_60_Days": int(sold_60),
            "Units_Sold_90_Days": int(sold_90),
            "Total_Units_Sold": int(total_sold),
            "Previous_Discount": float(prev_discount),
            "Channel": channel,
            "Location": location,
            "Season": season
        })
        
    df = pd.DataFrame(records)
    
    os.makedirs(output_dir, exist_ok=True)
    clean_brand = brand_name.lower().replace(" ", "_")
    csv_file = os.path.join(output_dir, f"{clean_brand}_sales_inventory.csv")
    xlsx_file = os.path.join(output_dir, f"{clean_brand}_sales_inventory.xlsx")
    
    df.to_csv(csv_file, index=False)
    df.to_excel(xlsx_file, index=False, engine="openpyxl")
    
    print(f"Generated {len(df)} records for '{brand_name}'")
    print(f"   -> CSV File:   {csv_file}")
    print(f"   -> Excel File: {xlsx_file}")
    
    return df

if __name__ == "__main__":
    # Fixed: brand_name matches the names already baked into your existing
    # spreadsheets ("JAK ..." not "JAK Threads ..."). Change this only if
    # you're okay with every Product_Name in your data shifting.
    generate_fashion_dataset(brand_name="JAK", n_samples=1200, output_dir="./data")
