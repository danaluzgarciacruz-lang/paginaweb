from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret-key-clave-supersegura"  # Cambiar por seguridad en producción

# ------------------ DB CONNECTION ------------------
def get_db():
    conn = sqlite3.connect("blog.db")
    conn.row_factory = sqlite3.Row
    return conn

# Crear tablas si no existen
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    conn.commit()
    conn.close()

init_db()

# ------------------ RUTAS ------------------
@app.route("/")
def index():
    conn = get_db()
    posts = conn.execute("""
        SELECT posts.*, users.username
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("index.html", posts=posts)

# Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("Todos los campos son obligatorios")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        conn = get_db()

        try:
            conn.execute("INSERT INTO users(username, password_hash) VALUES (?,?)",
                         (username, password_hash))
            conn.commit()
            flash("Usuario creado correctamente. Ahora inicia sesión")
            return redirect(url_for("login"))
        except:
            flash("El nombre de usuario ya existe")
        conn.close()

    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Usuario o contraseña incorrectos")

    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente")
    return redirect(url_for("index"))

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    posts = conn.execute("SELECT * FROM posts WHERE user_id=? ORDER BY created_at DESC",
                         (session["user_id"],)).fetchall()
    conn.close()
    return render_template("dashboard.html", posts=posts)

# Crear Post
@app.route("/create", methods=["POST"])
def create_post():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title")
    content = request.form.get("content")

    if not title or not content:
        flash("Todos los campos son obligatorios")
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute("INSERT INTO posts(title, content, user_id) VALUES (?,?,?)",
                 (title, content, session["user_id"]))
    conn.commit()
    conn.close()
    flash("Post creado exitosamente")
    return redirect(url_for("dashboard"))

# Editar Post
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_post(id):
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn.execute("UPDATE posts SET title=?, content=? WHERE id=?",
                     (title, content, id))
        conn.commit()
        conn.close()
        flash("Post actualizado")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit_post.html", post=post)

# Eliminar Post
@app.route("/delete/<int:id>")
def delete_post(id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Post eliminado")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
