import os
from supabase import create_client, Client

SUPABASE_URL = "https://wvxofntigjdexaiopgow.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2eG9mbnRpZ2pkZXhhaW9wZ293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkyMTk5MjQsImV4cCI6MjEwNDc5NTkyNH0.I5ifllBXVsPu5Rim51CgHnoZo2H_sscWWa2rFzJUwI0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

sample_products = [
    {
        "title": "گوشی هوشمند سامسونگ مدل Galaxy S24 Ultra",
        "category": "دیجیتال",
        "price": 72000000,
        "discount_price": 68500000,
        "description": "گوشی هوشمند پرچمدار سامسونگ با صفحه نمایش ۶.۸ اینچی، دوربین ۲۰۰ مگاپیکسلی حرفه‌ای، پشتیبانی از هوش مصنوعی گلکسی و قلم S-Pen.",
        "affiliate_link": "https://www.digikala.com",
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=600"
    },
    {
        "title": "لپ‌تاپ ۱۵.۶ اینچی ایسوس مدل TUF Gaming A15",
        "category": "دیجیتال",
        "price": 55000000,
        "discount_price": 51000000,
        "description": "لپ‌تاپ مخصوص بازی و کارهای سنگین مهندسی، مجهز به پردازنده AMD Ryzen 7، کارت گرافیک RTX 4060 و صفحه نمایش ۱۴۴ هرتز.",
        "affiliate_link": "https://www.digikala.com",
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600"
    },
    {
        "title": "ساعت هوشمند اپل واچ سری ۹",
        "category": "دیجیتال",
        "price": 24000000,
        "discount_price": 22500000,
        "description": "ساعت هوشمند اپل با صفحه نمایش رتینا روشن‌تر، قابلیت‌های پیشرفته سلامتی و سنسورهای دقیق پایش ورزشی.",
        "affiliate_link": "https://www.digikala.com",
        "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600"
    },
    {
        "title": "هودی مردانه مدل بیسیک کد H12",
        "category": "پوشاک",
        "price": 850000,
        "discount_price": 690000,
        "description": "هودی شیک و گرم مناسب فصل پاییز و زمستان، تهیه شده از الیاف پنبه و توکُرکی درجه یک.",
        "affiliate_link": "https://www.digikala.com",
        "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600"
    },
    {
        "title": "کتونی پیاده‌روی مردانه نایک مدل Air Zoom",
        "category": "پوشاک",
        "price": 3500000,
        "discount_price": 2900000,
        "description": "کفش کتانی اسپرت و سبک مناسب پیاده‌روی‌های طولانی و باشگاه، مجهز به فناوری کپسول هوا.",
        "affiliate_link": "https://www.digikala.com",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600"
    },
    {
        "title": "اسپیکر بلوتوثی قابل حمل جی‌بی‌ال مدل Charge 5",
        "category": "دیجیتال",
        "price": 9500000,
        "discount_price": 8900000,
        "description": "اسپیکر بلوتوثی ضد آب با صدای بیس فوق‌العاده قوی و باتری باکیفیت بالا.",
        "affiliate_link": "https://www.digikala.com",
        "image_url": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600"
    }
]

if __name__ == "__main__":
    for prod in sample_products:
        supabase.table("products").insert(prod).execute()
    print("محصولات نمونه با موفقیت به دیتابیس اضافه شدند!")
