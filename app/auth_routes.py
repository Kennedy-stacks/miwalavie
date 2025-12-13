from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from .extensions import db, login_manager
from .models import User


bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


@bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("store.products"))
    return render_template("register.html")


@bp.post("/register")
def register_post():
    if current_user.is_authenticated:
        return redirect(url_for("store.products"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.")
        return redirect(url_for("auth.register"))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("That email is already registered. Please log in.")
        return redirect(url_for("auth.login"))

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return redirect(url_for("store.products"))


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("store.products"))

    next_url = request.args.get("next")
    return render_template("login.html", next_url=next_url)


@bp.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("store.products"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    next_url = request.form.get("next")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    login_user(user)

    if next_url:
        return redirect(next_url)
    return redirect(url_for("store.products"))


@bp.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("store.index"))


# Insecure by design ("security through obscurity").
# A hidden link in the UI points here so the store owner can claim admin.
@bp.get("/admin-claim")
def admin_claim():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=url_for("auth.admin_claim")))

    return render_template("admin_claim.html")


@bp.post("/admin-claim")
def admin_claim_post():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=url_for("auth.admin_claim")))

    # No code by request; just a confirmation.
    confirm = request.form.get("confirm")
    if confirm != "yes":
        flash("Please confirm to continue.")
        return redirect(url_for("auth.admin_claim"))

    current_user.is_admin = True
    db.session.commit()

    flash("Admin enabled for your account.")
    return redirect(url_for("admin.dashboard"))
