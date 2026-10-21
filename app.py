from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ecovision-local-demo-change-before-deploy")
init_db()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    db = get_db()
    stats = {
        "reports": db.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
        "resolved": db.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'").fetchone()[0],
        "areas": db.execute("SELECT COUNT(DISTINCT location) FROM reports").fetchone()[0],
        "members": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
    }
    latest = db.execute("SELECT reports.*, users.name AS reporter FROM reports JOIN users ON users.id=reports.user_id ORDER BY reports.created_at DESC LIMIT 3").fetchall()
    db.close()
    return render_template("index.html", stats=stats, latest=latest)

@app.route("/reports")
def reports():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    sql = """SELECT reports.*, users.name AS reporter FROM reports
             JOIN users ON users.id=reports.user_id WHERE 1=1"""
    args = []
    if q:
        sql += " AND (reports.title LIKE ? OR reports.location LIKE ? OR reports.description LIKE ?)"
        args.extend([f"%{q}%"] * 3)
    if category in ("Pollution", "Waste", "Water", "Green spaces", "Wildlife"):
        sql += " AND reports.category=?"; args.append(category)
    if status in ("Open", "In progress", "Resolved"):
        sql += " AND reports.status=?"; args.append(status)
    sql += " ORDER BY reports.created_at DESC"
    db = get_db()
    items = db.execute(sql, args).fetchall()
    db.close()
    return render_template("reports.html", reports=items, q=q, category=category, status=status)

@app.route("/report/new", methods=["GET", "POST"])
@login_required
def new_report():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "")
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not location or not description or category not in ("Pollution", "Waste", "Water", "Green spaces", "Wildlife"):
            flash("Please complete all required fields.", "error")
            return render_template("new_report.html")
        db = get_db()
        db.execute("INSERT INTO reports (user_id,title,category,location,description,status) VALUES (?,?,?,?,?,'Open')",
                   (session["user_id"], title, category, location, description))
        db.commit(); db.close()
        flash("Your community observation has been submitted.", "success")
        return redirect(url_for("reports"))
    return render_template("new_report.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "error")
            return render_template("register.html")
        db = get_db()
        try:
            cur = db.execute("INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
                             (name, email, generate_password_hash(password)))
            db.commit()
            session["user_id"] = cur.lastrowid
            session["user_name"] = name
            flash("Welcome to EcoVision!", "success")
        except Exception:
            flash("That email may already be registered. Try signing in.", "error")
            db.close()
            return render_template("register.html")
        db.close()
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]; session["user_name"] = user["name"]
            flash("You are signed in.", "success")
            return redirect(url_for("index"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("index"))

@app.route("/report/<int:report_id>/resolve", methods=["POST"])
@login_required
def resolve_report(report_id):
    db = get_db()
    db.execute("UPDATE reports SET status='Resolved' WHERE id=? AND user_id=?", (report_id, session["user_id"]))
    db.commit(); db.close()
    flash("Your report status has been updated if it belongs to you.", "success")
    return redirect(request.referrer or url_for("reports"))

if __name__ == "__main__":
    app.run(debug=True)
