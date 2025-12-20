from flask import Blueprint, render_template, request, redirect, url_for, session
from data.db import get_connection
import services.auth_service

# Fix: store numeric `session['user_id']` on login to scope watchlist/ratings per user
auth = Blueprint("auth", __name__)
authService = services.auth_service.AuthService()

@auth.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if authService.authenticate(request.form["email"], request.form["password"]):
            email = request.form["email"]
            session["user"] = email
            # lookup numeric user id from centralized DB and store in session
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT UserID FROM users WHERE Email = ?", (email,))
                row = cur.fetchone()
                if row:
                    session['user_id'] = int(row['UserID'])
                conn.close()
            except Exception:
                pass
            return redirect(url_for("home.home"))
        else:
            error = "Invalid email or password"
    return render_template("Log_in.html", error=error)

@auth.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        if authService.register(request.form["email"], request.form["password"]):
            return redirect(url_for("auth.login"))
        else:
            error = "Email already registered"
    return render_template("Sign_up.html", error=error)

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.home"))
