def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # ایجاد جدول محصولات اگر وجود نداشته باشد
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            affiliate_link TEXT NOT NULL,
            image_url TEXT,
            price REAL DEFAULT 0,
            discount_price REAL DEFAULT 0,
            clicks INTEGER DEFAULT 0
        )
    ''')
    
    # بررسی و اضافه کردن ستون‌های جدید به جدول قدیمی (اگر وجود نداشتند)
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'price' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN price REAL DEFAULT 0")
    if 'discount_price' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN discount_price REAL DEFAULT 0")
    if 'clicks' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN clicks INTEGER DEFAULT 0")

    # جدول نظرات و امتیازات محصولات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            author TEXT NOT NULL,
            comment TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()
