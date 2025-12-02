import asyncio
import aiohttp
import random
import json
from typing import List

async def create_product(session: aiohttp.ClientSession, product_data: dict):
    url = "http://localhost/api/products/create"
    try:
        async with session.post(url, json=product_data) as response:
            if response.status == 201:
                print(f"✓ Created: {product_data['name']}")
            else:
                print(f"✗ Failed: {product_data['name']} - Status: {response.status}")
                error_text = await response.text()
                print(f"  Error: {error_text}")
    except Exception as e:
        print(f"✗ Exception: {product_data['name']} - {e}")

async def generate_and_upload_products():
    categories = {
        "electronics": ["Laptop", "Smartphone", "Tablet", "Headphones", "Monitor", "Keyboard", "Mouse", "Speaker"],
        "clothing": ["T-Shirt", "Jeans", "Jacket", "Shoes", "Hat", "Dress", "Sweater", "Shorts"],
        "home": ["Chair", "Desk", "Lamp", "Rug", "Curtains", "Pillow", "Blanket", "Mirror"],
        "books": ["Novel", "Textbook", "Cookbook", "Biography", "Mystery", "Fantasy", "Science", "History"],
        "sports": ["Basketball", "Football", "Tennis Racket", "Yoga Mat", "Dumbbells", "Running Shoes", "Bicycle"]
    }
    
    brands = ["Nike", "Samsung", "Apple", "Sony", "Adidas", "Dell", "HP", "Lenovo", "Microsoft", "Google"]
    
    products = []
    
    for i in range(1000):
        category = random.choice(list(categories.keys()))
        product_type = random.choice(categories[category])
        brand = random.choice(brands)
        
        product_data = {
            "name": f"{brand} {product_type} {i:04d}",
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock": random.randint(0, 200),
            "description": f"High-quality {product_type.lower()} from {brand}. Perfect for everyday use."
        }
        products.append(product_data)
    
    # Upload products concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [create_product(session, product) for product in products]
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    print("Generating and uploading 1000 test products...")
    asyncio.run(generate_and_upload_products())
    print("Finished uploading products!")