import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client
import hashlib

app = Flask(__name__)
app.secret_key = "your-super-secret-key-change-this"

SUPABASE_URL = "https://wvxofntigjdexaiopgow.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2eG9mbnRpZ2pkZXhhaW9wZ293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkyMTk5MjQsImV4cCI6MjEwNDc5NTkyNH0.I5ifllBXVsPu5Rim51CgHnoZo2H_sscWWa2rFzJUwI0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASSWORD = "admin"

@app.route("/")
def home():
    category = request.args.get("category")
    search_query = request.args.get("q")
    sort_by = request.args.get("sort", "newest")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)

    query = supabase.table("products").select("*")
    
    if category and category != "همه":
        query = query.eq("category", category)
    if search_query:
        query = query.ilike("title", f"%{search_query}%")
    if min_price is not None:
        query = query.gte("discount_price", min_price)
    if max_price is not None:
        query = query.lte("discount_price", max_price)
        
    if sort_by == "cheapest":
        query = query.order("discount_price", desc=False)
    elif sort_by == "expensive":
        query = query.order("discount_price", desc=True)
    else:
        query = query.order("id", desc=True)

    response = query.execute()
    products = response.data
    
    # گرفتن لیست مقالات وبلاگ برای سئو
    posts_res = supabase.table("posts").select("*").limit(3).execute()
    posts = posts_res.data

    return render_template("index.html", products=products, posts=posts, current_category=category or "همه")

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    res = supabase.table("products").select("*").eq("id", product_id).execute()
    if not res.data:
        return redirect(url_for("home"))
    product = res.data[0]
    
    related_res = supabase.table("products").select("*").eq("category", product["category"]).neq("id", product_id).limit(2).execute()
    related_products = related_res.data
    
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

@app.route("/compare")
def compare_products():
    product_ids = request.args.get("ids", "")
    if not product_ids:
        return redirect(url_for("home"))
    
    ids_list = [int(i) for i in product_ids.split(",") if i.isdigit()]
    if not ids_list:
        return redirect(url_for("home"))

    response = supabase.table("products").select("*").in_("id", ids_list).execute()
    return render_template("compare.html", products=response.data)

# --- سیستم احراز هویت کاربران ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = hashlib.sha256(request.form.get("password").encode()).hexdigest()
        try:
            supabase.table("users").insert({"email": email, "password": password}).execute()
            return redirect(url_for("login_user"))
        except:
            return render_template("register.html", error="این ایمیل قبلاً ثبت‌نام کرده است.")
    return render_template("register.html")

@app.route("/user-login", methods=["GET", "POST"])
def login_user():
    if request.method == "POST":
        email = request.form.get("email")
        password = hashlib.sha256(request.form.get("password").encode()).hexdigest()
        res = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
        if res.data:
            session["user_id"] = res.data[0]["id"]
            session["user_email"] = res.data[0]["email"]
            return redirect(url_for("home"))
        return render_template("user_login.html", error="ایمیل یا رمز عبور اشتباه است.")
    return render_template("user_login.html")

@app.route("/user-logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
    return redirect(url_for("home"))

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login_user"))
    
    user_id = session["user_id"]
    fav_res = supabase.table("favorites").select("product_id").eq("user_id", user_id).execute()
    prod_ids = [item["product_id"] for item in fav_res.data]
    
    favorite_products = []
    if prod_ids:
        p_res = supabase.table("products").select("*").in_("id", prod_ids).execute()
        favorite_products = p_res.data

    return render_template("profile.html", favorite_products=favorite_products)

@app.route("/toggle-favorite/<int:product_id>", methods=["POST"])
def toggle_favorite(product_id):
    if not session.get("user_id"):
        return jsonify({"status": "unauthorized"})
    
    user_id = session["user_id"]
    exist = supabase.table("favorites").select("*").eq("user_id", user_id).eq("product_id", product_id).execute()
    
    if exist.data:
        supabase.table("favorites").delete().eq("user_id", user_id).eq("product_id", product_id).execute()
        return jsonify({"status": "removed"})
    else:
        supabase.table("favorites").insert({"user_id": user_id, "product_id": product_id}).execute()
        return jsonify({"status": "added"})

# --- وبلاگ و مقالات ---
@app.route("/blog")
def blog():
    res = supabase.table("posts").select("*").order("id", desc=True).execute()
    return render_template("blog.html", posts=res.data)

@app.route("/blog/<int:post_id>")
def blog_detail(post_id):
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data:
        return redirect(url_for("blog"))
    return render_template("blog_detail.html", post=res.data[0])

# --- پنل مدیریت ادمین ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_product":
            supabase.table("products").insert({
                "title": request.form.get("title"),
                "category": request.form.get("category"),
                "price": int(request.form.get("price", 0)),
                "discount_price": int(request.form.get("discount_price", 0)),
                "description": request.form.get("description"),
                "affiliate_link": request.form.get("affiliate_link"),
                "image_url": request.form.get("image_url")
            }).execute()
        elif action == "add_post":
            supabase.table("posts").insert({
                "title": request.form.get("post_title"),
                "slug": request.form.get("post_slug"),
                "content": request.form.get("post_content"),
                "image_url": request.form.get("post_image")
            }).execute()
        return redirect(url_for("admin"))
        
    products_res = supabase.table("products").select("*").order("id", desc=True).execute()
    posts_res = supabase.table("posts").select("*").order("id", desc=True).execute()
    return render_template("admin.html", products=products_res.data, posts=posts_res.data)

@app.route("/admin/delete/<int:product_id>")
def delete_product(product_id):
    if not session.get("admin"):
        return redirect(url_for("login"))
    supabase.table("products").delete().eq("id", product_id).execute()
    return redirect(url_for("admin"))

@app.route("/admin/delete-post/<int:post_id>")
def delete_post(post_id):
    if not session.get("admin"):
        return redirect(url_for("login"))
    supabase.table("posts").delete().eq("id", post_id).execute()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
