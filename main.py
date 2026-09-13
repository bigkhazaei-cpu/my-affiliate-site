import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # کلید امنیتی برای مدیریت Session

# اتصال به دیتابیس Supabase از طریق Environment Variables (امن و استاندارد برای Render)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-supabase-anon-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------------------------------
# صفحه اصلی و فیلترها / جستجو / دسته‌بندی
# ----------------------------------------------------
@app.route("/")
def home():
    category = request.args.get("category", "همه")
    search_query = request.args.get("q", "")
    sort_by = request.args.get("sort", "newest")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)

    # کوئری پایه برای محصولات
    query = supabase.table("products").select("*")

    # فیلتر دسته‌بندی
    if category and category != "همه":
        query = query.eq("category", category)

    # فیلتر جستجو در عنوان
    if search_query:
        query = query.ilike("title", f"%{search_query}%")

    # فیلتر قیمت
    if min_price is not None:
        query = query.gte("discount_price", min_price)
    if max_price is not None:
        query = query.lte("discount_price", max_price)

    # مرتب‌سازی
    if sort_by == "cheapest":
        query = query.order("discount_price", desc=False)
    elif sort_by == "expensive":
        query = query.order("discount_price", desc=True)
    else:  # پیش‌فرض جدیدترین
        query = query.order("id", desc=True)

    products_res = query.execute()
    products = products_res.data

    # دریافت آخرین مقالات وبلاگ جهت نمایش در صفحه اصلی
    posts_res = supabase.table("posts").select("*").order("id", desc=True).limit(3).execute()
    posts = posts_res.data

    return render_template("index.html", products=products, posts=posts, current_category=category)

# ----------------------------------------------------
# صفحه جزئیات محصول، نظرات و محصولات مرتبط
# ----------------------------------------------------
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    res = supabase.table("products").select("*").eq("id", product_id).execute()
    if not res.data:
        return redirect(url_for("home"))
    product = res.data[0]
    
    # محصولات مشابه در همان دسته‌بندی
    related_res = supabase.table("products").select("*").eq("category", product["category"]).neq("id", product_id).limit(3).execute()
    related_products = related_res.data
    
    # دریافت نظرات محصول
    comments_res = supabase.table("comments").select("*").eq("product_id", product_id).order("id", desc=True).execute()
    comments = comments_res.data

    return render_template("product.html", product=product, related_products=related_products, comments=comments)

@app.route("/product/<int:product_id>/comment", methods=["POST"])
def add_comment(product_id):
    author = request.form.get("author")
    content = request.form.get("content")
    rating = request.form.get("rating", 5)
    
    if author and content:
        supabase.table("comments").insert({
            "product_id": product_id,
            "author": author,
            "content": content,
            "rating": int(rating)
        }).execute()
    return redirect(url_for("product_detail", product_id=product_id))

# ----------------------------------------------------
# مقایسه محصولات
# ----------------------------------------------------
@app.route("/compare")
def compare_products():
    ids_param = request.args.get("ids", "")
    products = []
    if ids_param:
        try:
            id_list = [int(i) for i in ids_param.split(",") if i.isdigit()]
            if id_list:
                res = supabase.table("products").select("*").in_("id", id_list).execute()
                products = res.data
        except ValueError:
            pass
    return render_template("compare.html", products=products)

# ----------------------------------------------------
# بخش مقالات و وبلاگ
# ----------------------------------------------------
@app.route("/blog")
def blog_list():
    res = supabase.table("posts").select("*").order("id", desc=True).execute()
    return render_template("blog.html", posts=res.data)

@app.route("/blog/<int:post_id>")
def blog_detail(post_id):
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data:
        return redirect(url_for("blog_list"))
    return render_template("blog_detail.html", post=res.data[0])

# ----------------------------------------------------
# سیستم احراز هویت کاربران (ثبت‌نام، ورود، خروج)
# ----------------------------------------------------
@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        res = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
        if res.data:
            session["user_id"] = res.data[0]["id"]
            session["user_email"] = res.data[0]["email"]
            return redirect(url_for("home"))
        return render_template("login.html", error="ایمیل یا رمز عبور اشتباه است.")
    return render_template("login.html")

@app.route("/user-register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # بررسی اینکه آیا کاربر قبلاً ثبت‌نام کرده است یا خیر
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return render_template("register.html", error="این ایمیل قبلاً ثبت‌نام کرده است.")
        
        # ثبت نام کاربر جدید در دیتابیس
        res = supabase.table("users").insert({"email": email, "password": password}).execute()
        if res.data:
            session["user_id"] = res.data[0]["id"]
            session["user_email"] = res.data[0]["email"]
            return redirect(url_for("home"))
            
        return render_template("register.html", error="خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.")
    return render_template("register.html")

@app.route("/user-logout")
def user_logout():
    session.clear()
    return redirect(url_for("home"))

# ----------------------------------------------------
# علاقه‌مندی‌ها (Favorites)
# ----------------------------------------------------
@app.route("/toggle-favorite/<int:product_id>", methods=["POST"])
def toggle_favorite(product_id):
    if "user_id" not in session:
        return jsonify({"status": "unauthorized"})
    
    user_id = session["user_id"]
    
    # بررسی وجود قبلی در علاقه‌مندی‌ها
    check = supabase.table("favorites").select("*").eq("user_id", user_id).eq("product_id", product_id).execute()
    
    if check.data:
        supabase.table("favorites").delete().eq("user_id", user_id).eq("product_id", product_id).execute()
        return jsonify({"status": "removed"})
    else:
        supabase.table("favorites").insert({"user_id": user_id, "product_id": product_id}).execute()
        return jsonify({"status": "added"})

@app.route("/profile")
def user_profile():
    if "user_id" not in session:
        return redirect(url_for("user_login"))
    
    user_id = session["user_id"]
    fav_res = supabase.table("favorites").select("product_id").eq("user_id", user_id).execute()
    product_ids = [item["product_id"] for item in fav_res.data]
    
    favorite_products = []
    if product_ids:
        prod_res = supabase.table("products").select("*").in_("id", product_ids).execute()
        favorite_products = prod_res.data
        
    return render_template("profile.html", favorite_products=favorite_products)

if __name__ == "__main__":
    app.run(debug=True, port=5000)