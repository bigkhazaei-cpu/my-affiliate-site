import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "your-super-secret-key-change-this"

# اتصال به دیتابیس Supabase
SUPABASE_URL = "https://wvxofntigjdexaiopgow.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2eG9mbnRpZ2pkZXhhaW9wZ293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkyMTk5MjQsImV4cCI6MjEwNDc5NTkyNH0.I5ifllBXVsPu5Rim51CgHnoZo2H_sscWWa2rFzJUwI0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASSWORD = "admin"  # رمز عبور پنل مدیریت

@app.route("/")
def home():
    category = request.args.get("category")
    search_query = request.args.get("q")
    sort_by = request.args.get("sort", "newest")

    query = supabase.table("products").select("*")
    
    if category and category != "همه":
        query = query.eq("category", category)
    if search_query:
        query = query.ilike("title", f"%{search_query}%")
        
    if sort_by == "cheapest":
        query = query.order("discount_price", desc=False)
    elif sort_by == "expensive":
        query = query.order("discount_price", desc=True)
    else:
        query = query.order("id", desc=True)

    response = query.execute()
    products = response.data
    return render_template("index.html", products=products, current_category=category or "همه")

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    res = supabase.table("products").select("*").eq("id", product_id).execute()
    if not res.data:
        return redirect(url_for("home"))
    product = res.data[0]
    
    # محصولات مرتبط
    related_res = supabase.table("products").select("*").eq("category", product["category"]).neq("id", product_id).limit(2).execute()
    related_products = related_res.data
    
    # نظرات محصول
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
        title = request.form.get("title")
        category = request.form.get("category")
        price = int(request.form.get("price", 0))
        discount_price = int(request.form.get("discount_price", 0))
        description = request.form.get("description")
        affiliate_link = request.form.get("affiliate_link")
        image_url = request.form.get("image_url")
        
        supabase.table("products").insert({
            "title": title,
            "category": category,
            "price": price,
            "discount_price": discount_price,
            "description": description,
            "affiliate_link": affiliate_link,
            "image_url": image_url
        }).execute()
        return redirect(url_for("admin"))
        
    products_res = supabase.table("products").select("*").order("id", desc=True).execute()
    return render_template("admin.html", products=products_res.data)

@app.route("/admin/delete/<int:product_id>")
def delete_product(product_id):
    if not session.get("admin"):
        return redirect(url_for("login"))
    supabase.table("products").delete().eq("id", product_id).execute()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
