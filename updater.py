import os
import requests

# تنظیمات اتصال به Supabase (استفاده از هاردکد URL یا متغیر محیطی)
SUPABASE_URL = "https://wvxofntigjdexaiopgow.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def fetch_digikala_top_products():
    """
    در اینجا باید منطق اسکرپ کردن یا گرفتن پرفروش‌ترین‌های دیجی‌کالا قرار گیرد.
    به عنوان نمونه، فرض کنید این لیست محصولات از دیجی‌کالا استخراج شده است:
    """
    # ساختار نمونه از محصولاتی که از دیجی‌کالا گرفتیم
    products_to_add = [
        {
            "title": "گوشی موبایل شیائومی مدل پرفروش روز",
            "price": 15000000,
            "discount_price": 12500000,
            "image_url": "https://...",
            "affiliate_url": "https://www.digikala.com/product/..."
        },
        # محصولات بیشتر...
    ]
    return products_to_add

def save_or_update_products(products):
    for product in products:
        # ارسال محصولات به جدول محصولات در Supabase
        url = f"{SUPABASE_URL}/rest/v1/products"
        
        # اگر از قبل وجود داشت آپدیت کند یا درج کند (بسته به ساختار جدول)
        response = requests.post(url, json=product, headers=headers)
        
        if response.status_code in [200, 201, 204]:
            print(f"محصول '{product['title']}' با موفقیت در سایت ثبت شد.")
        else:
            print(f"خطا در ثبت محصول: {response.text}")

if __name__ == "__main__":
    print("شروع دریافت پرفروش‌ترین‌های دیجی‌کالا...")
    top_products = fetch_digikala_top_products()
    save_or_update_products(top_products)
    print("عملیات روزانه با موفقیت به پایان رسید.")
