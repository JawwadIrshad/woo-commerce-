import json
import requests
import os
from dotenv import load_dotenv


load_dotenv()

# WooCommerce API credentials from .env
WC_CONSUMER_KEY = os.getenv('WC_CONSUMER_KEY')
WC_CONSUMER_SECRET = os.getenv('WC_CONSUMER_SECRET')
BASE_URL = os.getenv('WC_BASE_URL')
PRODUCTS_URL = f'{BASE_URL}/products'
CATEGORIES_URL = f'{BASE_URL}/products/categories'
CATEGORY_BATCH_URL = f'{BASE_URL}/products/categories/batch'

# Local JSON file
SOURCE_FILE = 'final9.json'

def fetch_categories():
    """Fetch all existing WooCommerce categories"""
    response = requests.get(
        CATEGORIES_URL,
        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
        params={'per_page': 100}  # Get all categories
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch categories: {response.status_code}")
        return []

def create_category(category_name):
    """Create a single category in WooCommerce"""
    data = {
        "name": category_name,
        "slug": category_name.lower().replace(' ', '-')
    }
    response = requests.post(
        CATEGORIES_URL,
        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )
    if response.status_code in [200, 201]:
        print(f"🆕 Created new category: {category_name}")
        return response.json()
    else:
        print(f"❌ Failed to create category '{category_name}': {response.status_code} - {response.text}")
        return None

def get_or_create_category(category_name, existing_categories):
    """Get existing category or create new one if it doesn't exist"""
    if not category_name:
        return None
    
    # Check if category exists
    for cat in existing_categories:
        if cat['name'].lower() == category_name.lower():
            return cat['id']
    
    # Create new category if not found
    new_category = create_category(category_name)
    if new_category:
        existing_categories.append(new_category)  # Add to our local list
        return new_category['id']
    return None

def process_products():
    """Main function to process and post products"""
    # Load product data
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Load existing categories
    categories = fetch_categories()
    
    # Process each product
    for i, product in enumerate(products, start=1):
        try:
            product_name = product.get('name', '')
            if not product_name:
                print(f"⏭️ Skipping product {i}: No name provided")
                continue
            
            # Clean product data
            product.pop('id', None)
            for field in ['price', 'regular_price', 'sale_price']:
                if field in product and product[field] is not None:
                    product[field] = str(product[field])
            
            product.setdefault('type', 'simple')
            
            # Handle categories
            if 'categories' in product and product['categories']:
                # Use the first category from JSON if provided
                category_name = product['categories'][0].get('name')
                category_id = get_or_create_category(category_name, categories)
            else:
                # Try to extract category from product name (first word)
                category_name = product_name.split()[0]
                category_id = get_or_create_category(category_name, categories)
            
            if not category_id:
                print(f"⏭️ Skipping product {i}: Could not determine category for '{product_name}'")
                continue
            
            product['categories'] = [{"id": category_id}]
            
            # Post product to WooCommerce
            response = requests.post(
                PRODUCTS_URL,
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers={"Content-Type": "application/json"},
                data=json.dumps(product)
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Product {i}: '{product_name}' posted successfully with category ID {category_id}.")
            else:
                print(f"❌ Failed to post product {i}: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"❌ Error posting product {i}: {str(e)}")

if __name__ == "__main__":
    print("🛒 Starting WooCommerce Product Import")
    print("------------------------------------")
    process_products()
    print("✅ Import process completed")