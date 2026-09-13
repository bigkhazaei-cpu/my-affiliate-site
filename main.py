import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-change-it")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
BUCKET_NAME = "product-images"

@app.route("/")
def home():
    search_query = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort", "newest").strip()
    page = int(request.args.get("page", 1))
    per_page = 8
    start = (page - 1) * per_page
    end = start + per_page - 1

    query = supabase.table("products").select("*", count="exact")

    if search_query:
        query = query.ilike("title", f"%{search_query}%")
    if category:
        query = query.eq("category", category)

    if sort_by == "newest":
        query = query.order("id", desc=True)
    elif sort_by == "price_asc":
        query = query.order("price", desc=False)
    elif sort_by == "price_desc":
        query = query.order("price", desc=True)
    else:
        query = query.order("id", desc=True)

    query = query.range(start, end)
    response = query.execute()
    products = response.data
    total_count = response.count if hasattr(response, 'count') and response.count is not None else len(products)
    
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    cat_response = supabase.table("products").select("category").execute()
    all_categories = list(set([item["category"] for item in cat_response.data if item.get("category")]))

    return render_template(
        "index.html",
        products=products,
        categories=all_categories,
        search_query=search_query,
        selected_category=category,
        sort_by=sort_by,
        current_page=page,
        total_pages=total_pages
    )

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    prod_resp = supabase.table("products").select("*").eq("id", product_id).execute()
    if not prod_resp.data:
        return "محصولی یافت نشد", 404
    product = prod_resp.data[0]

    rev_resp = supabase.table("reviews").select("*").eq("product_id", product_id).order("id", desc=True).execute()
    reviews = rev_resp.data

    related_products = []
    if product.get("category"):
        rel_resp = supabase.table("products").select("*").eq("category", product["category"]).neq("id", product_id).limit(4).execute()
        related_products = rel_resp.data

    return render_template("product_detail.html", product=product, reviews=reviews, related_products=related_products)

@app.route("/review/<int:product_id>", methods=["POST"])
def add_review(product_id):
    author = request.form.get("author")
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment")

    supabase.table("reviews").insert({
        "product_id": product_id,
        "author": author,
        "rating": rating,
        "comment": comment
    }).execute()

    return redirect(url_for("product_detail", product_id=product_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            flash("رمز عبور اشتباه است", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        price = float(request.form.get("price") or 0)
        discount_price = float(request.form.get("discount_price") or 0)
        description = request.form.get("description")
        affiliate_link = request.form.get("affiliate_link")

        image_url = ""
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_bytes = file.read()
            try:
                supabase.storage.from_(BUCKET_NAME).upload(
                    path=filename,
                    file=file_bytes,
                    file_options={"content-type": file.content_type}
                )
                image_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)
            except Exception as e:
                print(f"Error uploading image: {e}")

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

    prod_resp = supabase.table("products").select("*").order("id", desc=True).execute()
    return render_template("admin.html", products=prod_resp.data)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    supabase.table("products").delete().eq("id", product_id).execute()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
