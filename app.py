from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
from pathlib import Path
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import os

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fixflow.db"
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-demo-secret")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024  # 3 MB

DEMO_USERS = {
    "student": {"password": "student123", "role": "student", "name": "Demo Student"},
    "staff": {"password": "staff123", "role": "staff", "name": "Maintenance Staff"},
    "admin": {"password": "admin123", "role": "admin", "name": "Campus Admin"},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Reported',
                photo TEXT,
                created_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        if count == 0:
            demo_rows = [
                ("Aarav", "Plumbing / Water", "Hostel Block A - Room 204", "Water leakage near the washbasin.", "High", "Reported", None, "2026-11-01 09:30"),
                ("Diya", "Electrical", "Academic Block - Lab 2", "One ceiling light is not working.", "Medium", "In Progress", None, "2026-11-02 11:15"),
                ("Kabir", "Cleanliness", "Hostel Block B - Floor 1", "Common area needs cleaning.", "Low", "Resolved", None, "2026-11-02 14:00"),
            ]
            conn.executemany("""
                INSERT INTO complaints
                (student_name, category, location, description, priority, status, photo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, demo_rows)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to view that page.", "error")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = DEMO_USERS.get(username)
        if user and user["password"] == password:
            session["username"] = username
            session["role"] = user["role"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Login details didn't match. Try one of the demo accounts below.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as conn:
        if session["role"] == "student":
            rows = conn.execute(
                "SELECT * FROM complaints WHERE student_name = ? ORDER BY id DESC",
                (session["name"],)
            ).fetchall()
            # Demo student can see all sample records as well as their own submissions.
            if not rows:
                rows = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
        counts = {
            "total": conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],
            "reported": conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Reported'").fetchone()[0],
            "progress": conn.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress'").fetchone()[0],
            "resolved": conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0],
        }
    return render_template("dashboard.html", complaints=rows, counts=counts)

@app.route("/new", methods=["GET", "POST"])
@roles_required("student")
def new_complaint():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        if not category or not location or not description:
            flash("Please complete all required fields.", "error")
            return render_template("new_complaint.html")
        photo_name = None
        photo = request.files.get("photo")
        if photo and photo.filename:
            if not allowed_file(photo.filename):
                flash("Please upload a JPG, PNG, or WEBP image.", "error")
                return render_template("new_complaint.html")
            photo_name = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")
            photo.save(UPLOAD_DIR / photo_name)
        with get_db() as conn:
            conn.execute("""
                INSERT INTO complaints
                (student_name, category, location, description, priority, status, photo, created_at)
                VALUES (?, ?, ?, ?, ?, 'Reported', ?, ?)
            """, (session["name"], category, location, description, priority, photo_name,
                  datetime.now().strftime("%Y-%m-%d %H:%M")))
        flash("Your complaint has been submitted and is now marked as Reported.", "success")
        return redirect(url_for("dashboard"))
    return render_template("new_complaint.html")

@app.route("/update/<int:complaint_id>", methods=["POST"])
@roles_required("staff", "admin")
def update_status(complaint_id):
    status = request.form.get("status")
    if status not in {"Reported", "In Progress", "Resolved"}:
        flash("Invalid status.", "error")
    else:
        with get_db() as conn:
            conn.execute("UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
        flash(f"Complaint #{complaint_id} updated to {status}.", "success")
    return redirect(url_for("dashboard"))

@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.errorhandler(413)
def too_large(_error):
    flash("Image is too large. Please choose an image under 3 MB.", "error")
    return redirect(url_for("new_complaint"))

init_db()

if __name__ == "__main__":
    app.run(debug=True)
