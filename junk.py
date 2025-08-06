import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "https://api.sooq.africa/api/v1/products/all"
PARAMS = {
    "page": 0,
    "elementPerPage": 2,
    "key": "createdAt",
    "direction": "asc"
}
CHUNK_SIZE = 10
OUTPUT_FILE = "junk15.json"

def fetch_products():
    try:
        print(f"Fetching products from {BASE_URL}...")
        response = requests.get(BASE_URL, params=PARAMS, timeout=30)
        response.raise_for_status()
        return {
            "data": response.json(),
            "url": response.url,
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def process_products(response_data):
    if not response_data or 'data' not in response_data:
        print("No valid response data")
        return None
        
    data = response_data['data']
    if not data or 'products' not in data:
        print("No products found in response")
        return None
        
    all_products = data['products']
    total_products = len(all_products)
    num_chunks = (total_products + CHUNK_SIZE - 1) // CHUNK_SIZE  # Proper ceiling division
    
    # Create chunks
    chunks = []
    for i in range(num_chunks):
        start_idx = i * CHUNK_SIZE
        end_idx = start_idx + CHUNK_SIZE
        chunks.append({
            "chunk_id": f"chunk_{i+1:03d}",
            "products": all_products[start_idx:end_idx]
        })
    
    return {
        "fetch_time": datetime.now().isoformat(),
        "source_url": response_data['url'],
        "status_code": response_data['status_code'],
        "total_products": total_products,
        "total_chunks": num_chunks,
        "chunks": chunks
    }

def save_to_file(data):
    try:
        # Initialize with empty list if file doesn't exist
        if not os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'w') as f:
                json.dump([], f)
        
        # Read existing data
        with open(OUTPUT_FILE, 'r') as f:
            existing_data = json.load(f)
        
        # Append new data
        existing_data.append(data)
        
        # Write back to file
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)
            
        print(f"Saved {data['total_products']} products in {data['total_chunks']} chunks to {OUTPUT_FILE}")
        print(f"First chunk has {len(data['chunks'][0]['products'])} products")
        print(f"Last chunk has {len(data['chunks'][-1]['products'])} products")
    except Exception as e:
        print(f"Error saving to file: {e}")

def main():
    print("Junk Format Product Fetcher")
    print("--------------------------")
    
    response = fetch_products()
    if response:
        processed_data = process_products(response)
        if processed_data:
            save_to_file(processed_data)

if __name__ == "__main__":
    main()


# import requests
# import json
# import os
# import time
# from datetime import datetime
# from csv import writer

# # === Configuration ===
# BASE_URL = "https://api.sooq.africa/api/v1/products/all"
# PARAMS = {
#     "page": 0,
#     "elementPerPage": 400,
#     "key": "createdAt",
#     "direction": "asc"
# }
# CHUNK_SIZE = 10
# OUTPUT_FILE = "junk.json"
# LAST_GOOD_COUNT_FILE = "last_valid_count.txt"
# LOG_FILE = "fetch_log.csv"

# MAX_RETRIES = 10
# RETRY_DELAY = 3  # seconds
# FALLBACK_MIN_PRODUCTS = 50  # Used only if no history


# # === Helper Functions ===

# def get_last_good_count():
#     if os.path.exists(LAST_GOOD_COUNT_FILE):
#         with open(LAST_GOOD_COUNT_FILE, "r") as f:
#             try:
#                 return int(f.read().strip())
#             except:
#                 return None
#     return None

# def save_last_good_count(count):
#     with open(LAST_GOOD_COUNT_FILE, "w") as f:
#         f.write(str(count))

# def log_fetch_result(count, status):
#     exists = os.path.exists(LOG_FILE)
#     with open(LOG_FILE, "a", newline="") as f:
#         log = writer(f)
#         if not exists:
#             log.writerow(["timestamp", "product_count", "status"])
#         log.writerow([datetime.now().isoformat(), count, status])


# # === Fetch Products with Validation ===

# def fetch_products():
#     attempt = 0
#     last_good_count = get_last_good_count() or FALLBACK_MIN_PRODUCTS

#     while attempt < MAX_RETRIES:
#         try:
#             print(f"🔄 Fetching products (attempt {attempt + 1})...")
#             response = requests.get(BASE_URL, params=PARAMS, timeout=30)
#             response.raise_for_status()
#             json_data = response.json()

#             # Extract product list
#             products = json_data.get("products") or json_data.get("data", {}).get("products")
#             product_count = len(products) if products else 0

#             print(f"✅ Received {product_count} products")

#             # Validate product count
#             if product_count >= int(0.9 * last_good_count):
#                 print("✅ Product count is acceptable")
#                 log_fetch_result(product_count, "success")
#                 save_last_good_count(product_count)
#                 return {
#                     "data": json_data,
#                     "url": response.url,
#                     "status_code": response.status_code
#                 }
#             else:
#                 print(f"⚠️ Too few products ({product_count} < 90% of last good count {last_good_count}) — retrying...")
#                 log_fetch_result(product_count, "too_few")
#                 attempt += 1
#                 time.sleep(RETRY_DELAY)

#         except requests.exceptions.RequestException as e:
#             print(f"❌ Request failed (attempt {attempt + 1}): {e}")
#             log_fetch_result(0, "request_failed")
#             attempt += 1
#             time.sleep(RETRY_DELAY)

#     print("❌ Failed to fetch reliable product data after multiple attempts.")
#     return None


# # === Process and Chunk Data ===

# def process_products(response_data):
#     if not response_data or 'data' not in response_data:
#         print("🚫 No valid response data")
#         return None

#     data = response_data['data']
#     products = data.get('products') or data.get('data', {}).get('products')

#     if not products:
#         print("🚫 No products found in response")
#         return None

#     total_products = len(products)
#     num_chunks = (total_products + CHUNK_SIZE - 1) // CHUNK_SIZE

#     chunks = []
#     for i in range(num_chunks):
#         start_idx = i * CHUNK_SIZE
#         end_idx = start_idx + CHUNK_SIZE
#         chunks.append({
#             "chunk_id": f"chunk_{i + 1:03d}",
#             "products": products[start_idx:end_idx]
#         })

#     return {
#         "fetch_time": datetime.now().isoformat(),
#         "source_url": response_data['url'],
#         "status_code": response_data['status_code'],
#         "total_products": total_products,
#         "total_chunks": num_chunks,
#         "chunks": chunks
#     }


# # === Save Data to File ===

# def save_to_file(data):
#     try:
#         if not os.path.exists(OUTPUT_FILE):
#             with open(OUTPUT_FILE, 'w') as f:
#                 json.dump([], f)

#         with open(OUTPUT_FILE, 'r') as f:
#             existing_data = json.load(f)

#         existing_data.append(data)

#         with open(OUTPUT_FILE, 'w') as f:
#             json.dump(existing_data, f, indent=2)

#         print(f"💾 Saved {data['total_products']} products in {data['total_chunks']} chunks to {OUTPUT_FILE}")
#         print(f"📦 First chunk: {len(data['chunks'][0]['products'])} products")
#         print(f"📦 Last chunk: {len(data['chunks'][-1]['products'])} products")

#     except Exception as e:
#         print(f"❌ Error saving to file: {e}")


# # === Entry Point ===

# def main():
#     print("🚀 Junk Format Product Fetcher")
#     print("------------------------------")

#     response = fetch_products()
#     if response:
#         processed_data = process_products(response)
#         if processed_data:
#             save_to_file(processed_data)
#         else:
#             print("⚠️ No chunks created due to bad product data.")
#     else:
#         print("⚠️ No response to process.")

# if __name__ == "__main__":
#     main()
