from __future__ import annotations

import os
from datetime import datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from .extensions import db
from .models import Order, OrderItem, Product, User, format_ngn


bp = Blueprint("admin", __name__, url_prefix="/admin")


def _admin_required():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))
    if not getattr(current_user, "is_admin", False):
        abort(403)
    return None


@bp.before_request
def _guard_admin_routes():
    # All /admin routes require admin.
    res = _admin_required()
    if res is not None:
        return res


@bp.get("/")
def dashboard():
    return render_template("admin/dashboard.html")


@bp.get("/products")
def products():
    items = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=items, format_ngn=format_ngn)


@bp.post("/products")
def products_post():
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    price_raw = (request.form.get("price_ngn") or "").strip().replace(",", "")

    image = request.files.get("image")

    if not name or not description or not price_raw or not image:
        flash("Name, description, price, and an image are required.")
        return redirect(url_for("admin.products"))

    try:
        price_ngn = int(float(price_raw))
    except Exception:
        flash("Price must be a number.")
        return redirect(url_for("admin.products"))

    filename = secure_filename(image.filename or "")
    if not filename:
        flash("Please choose an image file.")
        return redirect(url_for("admin.products"))

    upload_folder = current_app.config.get("UPLOAD_FOLDER", "static/uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # Ensure uniqueness
    base, ext = os.path.splitext(filename)
    unique = f"{base}-{int(datetime.utcnow().timestamp())}{ext}".lower()

    save_path = os.path.join(upload_folder, unique)
    image.save(save_path)

    # store path relative to /static
    rel_path = os.path.relpath(save_path, start="static")

    p = Product(
        name=name,
        description=description,
        price_ngn=price_ngn,
        image_path=rel_path.replace("\\", "/"),
    )
    db.session.add(p)
    db.session.commit()

    flash("Product added.")
    return redirect(url_for("admin.products"))


@bp.post("/products/<int:product_id>/delete")
def products_delete(product_id: int):
    p = db.session.get(Product, product_id)
    if not p:
        flash("Product not found.")
        return redirect(url_for("admin.products"))

    db.session.delete(p)
    db.session.commit()
    flash("Product deleted.")
    return redirect(url_for("admin.products"))


@bp.get("/users")
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@bp.post("/users/<int:user_id>/toggle-admin")
def toggle_admin(user_id: int):
    if user_id == current_user.id:
        flash("You cannot change your own admin status here.")
        return redirect(url_for("admin.users"))

    u = db.session.get(User, user_id)
    if not u:
        flash("User not found.")
        return redirect(url_for("admin.users"))

    u.is_admin = not u.is_admin
    db.session.commit()
    return redirect(url_for("admin.users"))


@bp.get("/orders")
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()

    # eager-ish load items
    order_ids = [o.id for o in orders]
    items = (
        OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all()
        if order_ids
        else []
    )
    items_by_order: dict[int, list[OrderItem]] = {}
    for it in items:
        items_by_order.setdefault(it.order_id, []).append(it)

    return render_template(
        "admin/orders.html",
        orders=orders,
        items_by_order=items_by_order,
        format_ngn=format_ngn,
    )
