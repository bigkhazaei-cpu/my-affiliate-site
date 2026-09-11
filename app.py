import sqlite3
from flask import Flask, g, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_affiliate_key_123'
DATABASE = 'database.db'
ADMIN_PASSWORD = 'admin'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                slug TEXT UNIQUE NOT NULL,
                target_url TEXT NOT NULL,
                category TEXT DEFAULT 'عمومی',
                image_url TEXT,
                clicks INTEGER DEFAULT 0
            )
        ''')
        
        for col_name, col_type in [('category', "TEXT DEFAULT 'عمومی'"), ('image_url', 'TEXT'), ('clicks', 'INTEGER DEFAULT 0')]:
            try:
                cursor.execute(f'ALTER TABLE products ADD COLUMN {col_name} {col_type}')
                db.commit()
            except sqlite3.OperationalError:
                pass

        cursor.execute('SELECT COUNT(*) FROM products')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO products (title, description, slug, target_url, category, image_url, clicks)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            ''', ('گوشی هوشمند پرچمدار', 'بررسی تخصصی و خرید با تخفیف ویژه از معتبرترین فروشگاه آنلاین. این گوشی دارای دوربین قدرتمند و پردازنده فوق‌سریع است.', 'phone-offer', 'https://www.digikala.com', 'دیجیتال', 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500'))
            
            cursor.execute('''
                INSERT INTO products (title, description, slug, target_url, category, image_url, clicks)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            ''', ('هاست پرسرعت ابری', 'مناسب برای راه‌اندازی سایت‌های پربازدید با آپدیت و پشتیبانی ۲۴ ساعته و پهنای باند نامحدود.', 'hosting-deal', 'https://example.com', 'خدمات وب', 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=500'))
            
            db.commit()

@app.route('/')
def home():
    db = get_db()
    cursor = db.cursor()
    
    search_query = request.args.get('q', '')
    selected_category = request.args.get('cat', '')
    page = request.args.get('page', 1, type=int)
    per_page = 6  # تعداد محصولات در هر صفحه
    offset = (page - 1) * per_page
    
    query = 'SELECT * FROM products WHERE 1=1'
    count_query = 'SELECT COUNT(*) FROM products WHERE 1=1'
    params = []
    
    if search_query:
        query_filter = ' AND (title LIKE ? OR description LIKE ?)'
        query += query_filter
        count_query += query_filter
        params.extend([f'%{search_query}%', f'%{search_query}%'])
        
    if selected_category and selected_category != 'all':
        query_filter = ' AND category = ?'
        query += query_filter
        count_query += query_filter
        params.append(selected_category)
        
    # دریافت تعداد کل محصولات برای صفحه‌بندی
    cursor.execute(count_query, params)
    total_products = cursor.fetchone()[0]
    total_pages = (total_products + per_page - 1) // per_page if total_products > 0 else 1
    
    # اضافه کردن محدودیت صفحه به کوئری اصلی
    query += ' LIMIT ? OFFSET ?'
    cursor.execute(query, params + [per_page, offset])
    products = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT category FROM products')
    categories = [row['category'] for row in cursor.fetchall() if row['category']]
    
    return render_template('index.html', products=products, categories=categories, 
                           search_query=search_query, selected_category=selected_category, 
                           current_page=page, total_pages=total_pages)

@app.route('/product/<slug>')
def product_detail(slug):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE slug = ?', (slug,))
    product = cursor.fetchone()
    
    if not product:
        return "محصول مورد نظر یافت نشد.", 404
        
    return render_template('product_detail.html', product=product)

@app.route('/go/<slug>')
def affiliate_redirect(slug):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, target_url FROM products WHERE slug = ?', (slug,))
    product = cursor.fetchone()
    
    if product:
        product_id = product['id']
        target_url = product['target_url']
        cursor.execute('UPDATE products SET clicks = clicks + 1 WHERE id = ?', (product_id,))
        db.commit()
        return redirect(target_url, code=302)
    
    return "محصول مورد نظر یافت نشد.", 404

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = 'رمز عبور اشتباه است.'
    return render_template('login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        slug = request.form['slug']
        target_url = request.form['target_url']
        category = request.form['category']
        image_url = request.form['image_url']
        
        try:
            cursor.execute('''
                INSERT INTO products (title, description, slug, target_url, category, image_url, clicks)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            ''', (title, description, slug, target_url, category, image_url))
            db.commit()
        except sqlite3.IntegrityError:
            return "خطا: شناسه‌ی (Slug) این محصول تکراری است. لطفاً مقدار دیگری انتخاب کنید."
            
        return redirect(url_for('admin_panel'))
        
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return render_template('admin.html', products=products)

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)