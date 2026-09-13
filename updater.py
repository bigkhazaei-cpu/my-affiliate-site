import os
import requests

# قرار دادن مستقیم آدرس Supabase برای جلوگیری از خطای خوانش متغیر در گیت‌هاب
SUPABASE_URL = "https://wvxofntigjdexaiopgow.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def update_product_price(product_id, new_price):
    url = f"{SUPABASE_URL}/rest/v1/products?id=eq.{product_id}"
    
    payload = {
        "discount_price": new_price
    }
    
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code == 204:
        print(f"محصول با شناسه {product_id} با موفقیت به‌روزرسانی شد.")
    else:
        print(f"خطا در به‌روزرسانی محصول {product_id}: {response.text}")

if __name__ == "__main__":
    update_product_price(1, 21500000)
