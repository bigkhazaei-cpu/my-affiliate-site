import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def update_product_price(product_id, new_price):
    # فرض بر این است که نام ستون قیمت در دیتابیس شما discount_price یا price است
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
    # تست روی محصول با شناسه 1
    update_product_price(1, 21500000)
