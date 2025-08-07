import json
import requests
from bs4 import BeautifulSoup
import re
import os

SOURCE_FILE = "junk16.json"
PRODUCTS_OUTPUT_FILE = "final11.json"
FEATURES_FOLDER = "features"
FEATURES_BASE_URL = " "  

def format_description(html_content):
    if not html_content or not isinstance(html_content, str):
        return html_content
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all():
        tag.attrs = {}
    for p in soup.find_all('p'):
        if p.find('strong'):
            p.replace_with(f"\n\n{p.get_text().strip()}\n")
        else:
            p.replace_with(f"\n\n{p.get_text().strip()}")
    for ul in soup.find_all('ul'):
        items = [f"- {li.get_text().strip()}\n" for li in ul.find_all('li')]
        ul.replace_with('\n' + ''.join(items))
    text = soup.get_text()
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'([\u2022\u25AA\u25A0])\s+', '- ', text)
    return text.strip()

def map_product_to_woocommerce(product):
    stock_quantity = product.get("quantity", 0)
    stock_status = "outofstock" if stock_quantity <= 0 else "instock"
    product.setdefault('type', 'simple')
    product['manage_stock'] = True
    product['backorders'] = 'no'
    mapped = {
        "name": product.get("name"),
        "description": format_description(product.get("description", "")),
        "short_description": product.get("alias", ""),
        "price": product.get("price"),
        "regular_price": product.get("price"),
        "sale_price": product.get("offerPrice"),
        "id": product.get("publicId"),
        "stock_quantity": stock_quantity,
        "stock_status": stock_status,
        "tax_status": "taxable" if product.get("taxable") else "none",
        "images": [{"src": product.get("image_url")}] if product.get("image_url") else [],
        "on_sale": product.get("onOffer", False),
        "categories": []
    }
    if product.get("departmentResponse"):
        mapped["categories"].append({
            "id": 1,
            "name": product["departmentResponse"].get("name"),
            "slug": (product.get("listingSectionResponse", {}).get("name") or "").lower().replace(" ", "-")
        })
    return mapped

def process_products():
    # Create the features folder if it doesn't exist
    os.makedirs(FEATURES_FOLDER, exist_ok=True)

    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {SOURCE_FILE}: {str(e)}")
        return []

    products_result = []
    seen_names = set()
    feature_count = 0

    for entry in data:
        for chunk in entry.get("chunks", []):
            for product in chunk.get("products", []):
                try:
                    mapped = map_product_to_woocommerce(product)
                    name_key = mapped.get("name", "").strip().lower()
                    if name_key and name_key not in seen_names:
                        products_result.append(mapped)
                        seen_names.add(name_key)

                        public_id = product.get("publicId")
                        if public_id:
                            url = FEATURES_BASE_URL.format(public_id)
                            try:
                                response = requests.get(url)
                                if response.status_code == 200:
                                    feature_data = response.json()
                                    feature_count += 1
                                    feature_file = os.path.join(FEATURES_FOLDER, f"feature{feature_count}.json")
                                    with open(feature_file, 'w', encoding='utf-8') as f:
                                        json.dump({"publicId": public_id, "features": feature_data}, f, indent=2, ensure_ascii=False)
                                    print(f"✅ Saved {feature_file}")
                                else:
                                    print(f"⚠️ Failed to fetch features for {public_id}")
                            except Exception as e:
                                print(f"❌ Error fetching features for {public_id}: {str(e)}")
                except Exception as e:
                    print(f"⚠️ Error processing product: {str(e)}")
                    continue

    # Save products data
    try:
        with open(PRODUCTS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(products_result, f, indent=2, ensure_ascii=False)
        print(f"✅ Products saved to {PRODUCTS_OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving products: {str(e)}")

if __name__ == "__main__":
    print("🛒 WooCommerce Product + Features Fetcher")
    print("-----------------------------------------")
    process_products()
    print("✅ All done.")
