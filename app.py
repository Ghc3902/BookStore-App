# Flask Bookstore Application
# Hruthik Gorantla – CS665 Project

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

DATABASE = "bookstore_db.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin123":
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # Safely try to read counts if tables exist
    def safe_count(table):
        try:
            cur.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
            return cur.fetchone()["cnt"]
        except Exception:
            return 0

    books_count = safe_count("Books")
    customers_count = safe_count("Customers")
    orders_count = safe_count("Orders")

    conn.close()
    return render_template("dashboard.html",
                           books_count=books_count,
                           customers_count=customers_count,
                           orders_count=orders_count)

@app.route("/books")
@login_required
def list_books():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM Books")
        books = cur.fetchall()
    except Exception:
        books = []
    conn.close()
    return render_template("books_list.html", books=books)
# ---------------- CUSTOMERS LIST ----------------

@app.route("/customers")
@login_required
def list_customers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Customers")
    customers = cur.fetchall()
    conn.close()
    return render_template("customers_list.html", customers=customers)


@app.route("/books/add", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        genre = request.form.get("genre")
        price = request.form.get("price")
        stock = request.form.get("stock")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Books (Title, Author, Genre, Price, Stock) VALUES (?, ?, ?, ?, ?)",
            (title, author, genre, price, stock),
        )
        conn.commit()
        conn.close()

        flash("Book added successfully!", "success")
        return redirect(url_for("list_books"))

    return render_template("books_form.html", action="Add", book=None)

@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        genre = request.form.get("genre")
        price = request.form.get("price")
        stock = request.form.get("stock")

        cur.execute(
            "UPDATE Books SET Title = ?, Author = ?, Genre = ?, Price = ?, Stock = ? WHERE BookID = ?",
            (title, author, genre, price, stock, book_id),
            )
        conn.commit()
        conn.close()
        flash("Book updated successfully!", "success")
        return redirect(url_for("list_books"))

    cur.execute("SELECT * FROM Books WHERE BookID = ?", (book_id,))
    book = cur.fetchone()
    conn.close()
    return render_template("books_form.html", action="Edit", book=book)
# ---------------- DATA VISUALIZATION ----------------

@app.route("/visualization")
@login_required
def visualization():

    conn = get_db_connection()
    cur = conn.cursor()

    # BOOK STOCK BAR CHART
    cur.execute("SELECT Title, Stock FROM Books")
    book_rows = cur.fetchall()
    book_labels = [row["Title"] for row in book_rows]
    book_values = [row["Stock"] for row in book_rows]

    # ORDERS PER DAY LINE CHART
    cur.execute("SELECT OrderDate, COUNT(*) as Total FROM Orders GROUP BY OrderDate")
    order_rows = cur.fetchall()
    order_labels = [row["OrderDate"] for row in order_rows]
    order_values = [row["Total"] for row in order_rows]

    conn.close()

    return render_template(
        "visualization.html",
        book_labels=book_labels,
        book_values=book_values,
        order_labels=order_labels,
        order_values=order_values
    )






if __name__ == "__main__":
    app.run(debug=True)
