import csv
import random
from datetime import date, timedelta
from pathlib import Path


random.seed(42)
output = Path(__file__).parent / "data" / "sample_sales.csv"
output.parent.mkdir(exist_ok=True)

products = {
    "Field Notebook": (12.0, "Stationery"),
    "Desk Lamp": (48.0, "Office"),
    "Travel Mug": (24.0, "Accessories"),
    "Canvas Tote": (18.0, "Accessories"),
    "Wireless Mouse": (36.0, "Electronics"),
    "Weekly Planner": (16.0, "Stationery"),
}
regions = ["North", "South", "East", "West"]
salespeople = ["Avery", "Jordan", "Morgan", "Riley", "Taylor"]
channels = ["Online", "Retail", "Partner"]
today = date.today()

with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Order Date", "Order ID", "Product", "Category", "Region", "Salesperson", "Quantity", "Unit Price", "Sales", "Channel"])
    order_number = 1001
    for offset in range(89, -1, -1):
        current_day = today - timedelta(days=offset)
        for _ in range(random.randint(5, 13)):
            product, (price, category) = random.choice(list(products.items()))
            quantity = random.choices([1, 2, 3, 4], weights=[55, 28, 12, 5])[0]
            unit_price = round(price * random.choice([0.9, 1.0, 1.0, 1.0, 1.1]), 2)
            writer.writerow([
                current_day.isoformat(), f"DB-{order_number}", product, category,
                random.choice(regions), random.choice(salespeople), quantity,
                unit_price, round(quantity * unit_price, 2), random.choice(channels),
            ])
            order_number += 1

print(f"Wrote {order_number - 1001} sample orders to {output}")