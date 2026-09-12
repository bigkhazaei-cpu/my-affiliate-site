import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key_affiliate"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
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
    
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'price' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN price REAL DEFAULT 0")
    if 'discount_price' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN discount_price REAL DEFAULT 0")
    if 'clicks' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN clicks INTEGER DEFAULT 0")

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

init_db()

@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ""')
    categories = [row['category'] for row in cursor.fetchall()]
    
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    
    if search_query:
        query += ' AND (title LIKE ? OR description LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])
        
    if selected_category:
        query += ' AND category = ?'
        params.append(selected_category)
        
    query += ' ORDER BY id DESC'
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', products=products, categories=categories, 
                           search_query=search_query, selected_category=selected_category)

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if request.method == 'POST':
        author = request.form.get('author')
        comment = request.form.get('comment')
        rating = int(request.form.get('rating', 5))
        if author and comment:
            cursor.execute('INSERT INTO reviews (product_id, author, comment, rating) VALUES (?, ?, ?, ?)',
                           (product_id, author, comment, rating))
            conn.commit()
        return redirect(url_for('product_detail', product_id=product_id))
    
    cursor.execute('UPDATE products SET clicks = clicks + 1 WHERE id = ?', (product_id,))
    conn.commit()
    
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    
    cursor.execute('SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC', (product_id,))
    reviews = cursor.fetchall()
    conn.close()
    
    if not product:
        return "محصول مورد نظر یافت نشد", 404
        
    return render_template('product_detail.html', product=product, reviews=reviews)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "admin123":
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "رمز عبور اشتباه است."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY id DESC')
    products = cursor.fetchall()
    conn.close()
    return render_template('admin.html', products=products)

@app.route('/admin/add', methods=['POST'])
def admin_add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    affiliate_link = request.form.get('affiliate_link')
    price = float(request.form.get('price') or 0)
    discount_price = float(request.form.get('discount_price') or 0)
    
    image_url = ""
    file = request.files.get('image_file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_url = f'/static/uploads/{filename}'
    else:
        image_url = request.form.get('image_url_text', '')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (title, description, category, affiliate_link, image_url, price, discount_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, category, affiliate_link, image_url, price, discount_price))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:product_id>')
def admin_delete(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    cursor.execute('DELETE FROM reviews WHERE product_id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)