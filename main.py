import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super_secret_key_change_me"

# پایگاه داده موقت در حافظه (برای نمونه‌سازی)
products = [
    {
        "id": 1,
        "title": "گوشی هوشمند پرچمدار",
        "category": "دیجیتال",
        "price": 45000000,
        "discount_price": 42000000,
        "description": "بررسی تخصصی و خرید با تخفیف ویژه از معتبرترین فروشگاه آنلاین.",
        "affiliate_link": "#",
        "image_url": ""
    }
]

reviews = {
    1: [
        {"author": "علی", "rating": 5, "comment": "عالی بود، کاملاً راضی هستم."}
    ]
}

@app.route("/")
def home():
    search_query = request.args.get("search", "")
    selected_category = request.args.get("category", "")
    
    filtered_products = products
    if search_query:
        filtered_products = [p for p in filtered_products if search_query in p["title"] or search_query in p["description"]]
    if selected_category:
        filtered_products = [p for p in filtered_products if p["category"] == selected_category]
        
    categories = list(set(p["category"] for p in products if p.get("category")))
    
    return render_template("index.html", products=filtered_products, categories=categories, search_query=search_query, selected_category=selected_category)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return "محصول یافت نشد", 404
    prod_reviews = reviews.get(product_id, [])
    return render_template("product_detail.html", product=product, reviews=prod_reviews)

@app.route("/product/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    author = request.form.get("author")
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment")
    
    if product_id not in reviews:
        reviews[product_id] = []
        
    reviews[product_id].append({
        "author": author,
        "rating": rating,
        "comment": comment
    })
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
        
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        price = int(request.form.get("price") or 0)
        discount_price = int(request.form.get("discount_price") or 0)
        description = request.form.get("description")
        affiliate_link = request.form.get("affiliate_link")
        
        new_id = max([p["id"] for p in products], default=0) + 1
        
        products.append({
            "id": new_id,
            "title": title,
            "category": category,
            "price": price,
            "discount_price": discount_price,
            "description": description,
            "affiliate_link": affiliate_link,
            "image_url": ""
        })
        return redirect(url_for("admin"))
        
    return render_template("admin.html", products=products)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
        
    global products
    products = [p for p in products if p["id"] != product_id]
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
