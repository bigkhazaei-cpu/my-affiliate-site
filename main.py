import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "super_secret_key_change_me"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# آدرس اتصال به Supabase (لطفاً رمز عبور و شناسه پروژه خود را جایگزین کنید)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# راه‌اندازی جدول‌ها در Supabase
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            price INTEGER,
            discount_price INTEGER,
            description TEXT,
            affiliate_link TEXT,
            image_url TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            author TEXT,
            rating INTEGER,
            comment TEXT
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route("/")
def home():
    search_query = request.args.get("search", "").strip()
    selected_category = request.args.get("category", "").strip()
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    if selected_category:
        query += " AND category = %s"
        params.append(selected_category)
        
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    categories = [row['category'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template("index.html", products=products, categories=categories, search_query=search_query, selected_category=selected_category)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        cursor.close()
        conn.close()
        return "محصول یافت نشد", 404
        
    cursor.execute("SELECT * FROM reviews WHERE product_id = %s", (product_id,))
    reviews = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("product_detail.html", product=product, reviews=reviews)

@app.route("/product/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    author = request.form.get("author")
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reviews (product_id, author, rating, comment) VALUES (%s, %s, %s, %s)",
                   (product_id, author, rating, comment))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for("product_detail", product_id=product_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "admin123":
            session["logged_in"] = True
            return redirect(url_for("admin"))
    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        price = int(request.form.get("price") or 0)
        discount_price = int(request.form.get("discount_price") or 0)
        description = request.form.get("description")
        affiliate_link = request.form.get("affiliate_link")
        
        image_url = ""
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            filename = f"{int(time.time())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')
            
        cursor.execute('''
            INSERT INTO products (title, category, price, discount_price, description, affiliate_link, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (title, category, price, discount_price, description, affiliate_link, image_url))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("admin"))
        
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin.html", products=products)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
