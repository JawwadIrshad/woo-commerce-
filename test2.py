import json
from bs4 import BeautifulSoup
import re

SOURCE_FILE = "junk14.json"
OUTPUT_FILE = "final9.json"

def format_description(html_content):
    """Convert HTML to perfectly formatted plain text with structure"""
    if not html_content or not isinstance(html_content, str):
        return html_content
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove all HTML attributes
    for tag in soup.find_all():
        tag.attrs = {}
    
    # Process paragraphs with strong tags (convert to headings)
    for p in soup.find_all('p'):
        if p.find('strong'):
            strong_text = p.get_text().strip()
            p.replace_with(f"\n\n{strong_text}\n")
        else:
            p.replace_with(f"\n\n{p.get_text().strip()}")
    
    # Process lists
    for ul in soup.find_all('ul'):
        list_items = []
        for li in ul.find_all('li'):
            # Remove <strong> tags but keep their text
            for strong in li.find_all('strong'):
                strong.unwrap()
            li_text = li.get_text().strip()
            list_items.append(f"- {li_text}\n")
        ul.replace_with('\n' + ''.join(list_items))
    
    # Get clean text
    text = soup.get_text()
    
    # Final cleanup
    text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive newlines
    text = re.sub(r'([•▪■])\s+', '- ', text)  # Convert bullets to hyphens
    text = text.strip()
    
    return text

def map_product_to_woocommerce(product):
    """Map the source product to WooCommerce format"""
    mapped = {
        "name": product.get("name"),
        "description": format_description(product.get("description", "")),
        "short_description": product.get("alias", ""),
        "price": product.get("price"),
        "regular_price": product.get("price"),
        "sale_price": product.get("offerPrice"),
        "id": product.get("publicId"),
        "stock_quantity": product.get("quantity"),
        "stock_status": "instock" if product.get("available") else "outofstock",
        "tax_status": "taxable" if product.get("taxable") else "none",
        "images": [{"src": product.get("image_url")}] if product.get("image_url") else [],
        "on_sale": product.get("onOffer", False),
        "categories": []
    }
    
    # Add category if available
    if product.get("departmentResponse"):
        mapped["categories"].append({
            "id": 1,
            "name": product["departmentResponse"].get("name"),
            "slug": (product.get("listingSectionResponse", {}).get("name") or "").lower().replace(" ", "-")
        })
    
    return mapped

def process_products():
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {SOURCE_FILE}: {str(e)}")
        return []
    
    results = []
    processed_count = 0
    
    for entry in data:
        for chunk in entry.get("chunks", []):
            for product in chunk.get("products", []):
                try:
                    mapped = map_product_to_woocommerce(product)
                    if mapped.get("name"):  # Only include products with names
                        results.append(mapped)
                        processed_count += 1
                except Exception as e:
                    print(f"⚠️ Error processing product: {str(e)}")
                    continue
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Successfully processed {processed_count} products")
        return True
    except Exception as e:
        print(f"❌ Error saving to {OUTPUT_FILE}: {str(e)}")
        return False

if __name__ == "__main__":
    print("🛒 WooCommerce Product Processor")
    print("-------------------------------")
    print(f"Processing {SOURCE_FILE}...")
    process_products()
    print(f"📁 Output saved to {OUTPUT_FILE}")