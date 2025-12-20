from flask import Blueprint, render_template, request, redirect, url_for, session
import services.auth_service

auth = Blueprint("auth", __name__)
authService = services.auth_service.AuthService()

@auth.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if authService.authenticate(request.form["email"], request.form["password"]):
            session["user"] = request.form["email"]
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
