import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-supabase-anon-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    category = request.args.get("category", "همه")
    search_query = request.args.get("q", "")
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

    try:
        products_res = query.execute()
        products = products_res.data if products_res and products_res.data else []
    except Exception as e:
        print("Error fetching products:", e)
        products = []

    try:
        posts_res = supabase.table("posts").select("*").order("id", desc=True).limit(3).execute()
        posts = posts_res.data if posts_res and posts_res.data else []
    except Exception as e:
        print("Error fetching posts:", e)
        posts = []

    return render_template("index.html", products=products, posts=posts, current_category=category)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    try:
        res = supabase.table("products").select("*").eq("id", product_id).execute()
        if not res.data:
            return redirect(url_for("home"))
        product = res.data[0]
        
        related_res = supabase.table("products").select("*").eq("category", product["category"]).neq("id", product_id).limit(3).execute()
        related_products = related_res.data if related_res.data else []
        
        comments_res = supabase.table("comments").select("*").eq("product_id", product_id).order("id", desc=True).execute()
        comments = comments_res.data if comments_res.data else []
    except Exception as e:
        print("Error fetching product details:", e)
        return redirect(url_for("home"))

    return render_template("product.html", product=product, related_products=related_products, comments=comments)

@app.route("/product/<int:product_id>/comment", methods=["POST"])
def add_comment(product_id):
    author = request.form.get("author")
    content = request.form.get("content")
    rating = request.form.get("rating", 5)
    
    if author and content:
        try:
            supabase.table("comments").insert({
                "product_id": product_id,
                "author": author,
                "content": content,
                "rating": int(rating)
            }).execute()
        except Exception as e:
            print("Error adding comment:", e)
    return redirect(url_for("product_detail", product_id=product_id))

# --- بخش سبد خرید (Cart) ---
@app.route("/cart")
def view_cart():
    if "user_id" not in session:
        return redirect(url_for("user_login"))
    
    user_id = session["user_id"]
    cart_items = []
    total_price = 0
    
    try:
        res = supabase.table("cart").select("id, quantity, product_id").eq("user_id", user_id).execute()
        items = res.data if res.data else []
        
        for item in items:
            prod_res = supabase.table("products").select("*").eq("id", item["product_id"]).execute()
            if prod_res.data:
                product = prod_res.data[0]
                subtotal = product["discount_price"] * item["quantity"]
                total_price += subtotal
                cart_items.append({
                    "cart_id": item["id"],
                    "product": product,
                    "quantity": item["quantity"],
                    "subtotal": subtotal
                })
    except Exception as e:
        print("Error fetching cart:", e)
        
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    if "user_id" not in session:
        return jsonify({"status": "unauthorized"})
    
    user_id = session["user_id"]
    try:
        existing = supabase.table("cart").select("*").eq("user_id", user_id).eq("product_id", product_id).execute()
        if existing.data:
            new_qty = existing.data[0]["quantity"] + 1
            supabase.table("cart").update({"quantity": new_qty}).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("cart").insert({"user_id": user_id, "product_id": product_id, "quantity": 1}).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        print("Add to cart error:", e)
        return jsonify({"status": "error"})

@app.route("/cart/remove/<int:cart_id>", methods=["POST"])
def remove_from_cart(cart_id):
    if "user_id" not in session:
        return redirect(url_for("user_login"))
    try:
        supabase.table("cart").delete().eq("id", cart_id).execute()
    except Exception as e:
        print("Remove from cart error:", e)
    return redirect(url_for("view_cart"))

# --- بخش بلاگ و مقالات ---
@app.route("/blog")
def blog_list():
    try:
        res = supabase.table("posts").select("*").order("id", desc=True).execute()
        posts = res.data if res.data else []
    except Exception as e:
        print("Error fetching blog posts:", e)
        posts = []
    return render_template("blog.html", posts=posts)

@app.route("/blog/create", methods=["GET", "POST"])
def create_post():
    if "user_id" not in session:
        return redirect(url_for("user_login"))
        
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        image_url = request.form.get("image_url")
        author = session.get("user_name", session.get("user_email", "مدیر"))
        
        if title and content:
            try:
                supabase.table("posts").insert({
                    "title": title,
                    "content": content,
                    "image_url": image_url,
                    "author": author
                }).execute()
                return redirect(url_for("blog_list"))
            except Exception as e:
                print("Error creating post:", e)
                return render_template("create_post.html", error="خطا در ثبت مقاله. لطفاً مجدد تلاش کنید.")
                
    return render_template("create_post.html")

@app.route("/blog/<int:post_id>")
def blog_detail(post_id):
    try:
        res = supabase.table("posts").select("*").eq("id", post_id).execute()
        if not res.data:
            return redirect(url_for("blog_list"))
        post = res.data[0]
    except Exception as e:
        print("Error fetching blog detail:", e)
        return redirect(url_for("blog_list"))
    return render_template("blog_detail.html", post=post)

# --- احراز هویت و حساب کاربری ---
@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            res = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
            if res.data:
                user = res.data[0]
                session["user_id"] = user["id"]
                session["user_email"] = user["email"]
                session["user_name"] = user.get("name", "")
                session["user_phone"] = user.get("phone", "")
                return redirect(url_for("home"))
        except Exception as e:
            print("Login error:", e)
            
        return render_template("login.html", error="ایمیل یا رمز عبور اشتباه است.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            existing = supabase.table("users").select("*").eq("email", email).execute()
            if existing.data:
                return render_template("register.html", error="این ایمیل قبلاً ثبت‌نام کرده است.")
            
            res = supabase.table("users").insert({"email": email, "password": password}).execute()
            if res.data:
                user = res.data[0]
                session["user_id"] = user["id"]
                session["user_email"] = user["email"]
                session["user_name"] = user.get("name", "")
                session["user_phone"] = user.get("phone", "")
                return redirect(url_for("home"))
        except Exception as e:
            print("Register error:", e)
            
        return render_template("register.html", error="خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.")
    return render_template("register.html")

@app.route("/user-logout")
def user_logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    return redirect(url_for("user_logout"))

@app.route("/toggle-favorite/<int:product_id>", methods=["POST"])
def toggle_favorite(product_id):
    if "user_id" not in session:
        return jsonify({"status": "unauthorized"})
    
    user_id = session["user_id"]
    try:
        check = supabase.table("favorites").select("*").eq("user_id", user_id).eq("product_id", product_id).execute()
        if check.data:
            supabase.table("favorites").delete().eq("user_id", user_id).eq("product_id", product_id).execute()
            return jsonify({"status": "removed"})
        else:
            supabase.table("favorites").insert({"user_id": user_id, "product_id": product_id}).execute()
            return jsonify({"status": "added"})
    except Exception as e:
        print("Favorite toggle error:", e)
        return jsonify({"status": "error"})

@app.route("/profile")
def user_profile():
    if "user_id" not in session:
        return redirect(url_for("user_login"))
    
    user_id = session["user_id"]
    try:
        user_res = supabase.table("users").select("*").eq("id", user_id).execute()
        if user_res.data:
            user = user_res.data[0]
            session["user_name"] = user.get("name", "")
            session["user_phone"] = user.get("phone", "")
    except Exception as e:
        print("Fetch user info error:", e)

    favorite_products = []
    try:
        fav_res = supabase.table("favorites").select("product_id").eq("user_id", user_id).execute()
        product_ids = [item["product_id"] for item in fav_res.data] if fav_res.data else []
        if product_ids:
            prod_res = supabase.table("products").select("*").in_("id", product_ids).execute()
            favorite_products = prod_res.data if prod_res.data else []
    except Exception as e:
        print("Profile favorites error:", e)
        
    return render_template("profile.html", favorite_products=favorite_products)

@app.route("/profile/update", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("user_login"))
    
    user_id = session["user_id"]
    name = request.form.get("name")
    phone = request.form.get("phone")
    
    try:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if phone is not None:
            update_data["phone"] = phone
            
        if update_data:
            supabase.table("users").update(update_data).eq("id", user_id).execute()
            if name is not None:
                session["user_name"] = name
            if phone is not None:
                session["user_phone"] = phone
    except Exception as e:
        print("Update profile error:", e)
            
    return redirect(url_for("user_profile"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
