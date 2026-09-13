import os
import requests
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def update_product(product_id, price, stock):
    url = f"{SUPABASE_URL}/rest/v1/products?id=eq.{product_id}"
    payload = {
        "discount_price": price,
        "stock": stock,
        "updated_at": datetime.now().isoformat()
    }
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code == 204:
        print(f"محصول {product_id} با موفقیت به‌روزرسانی شد.")
    else:
        print(f"خطا در به‌روزرسانی محصول {product_id}: {response.text}")

if __name__ == "__main__":
    # تست نمونه برای یک محصول (شناسه، قیمت جدید، موجودی جدید)
    update_product(1, 21500000, 15)