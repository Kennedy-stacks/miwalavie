from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Order, OrderItem, OrderMessage, Product, format_ngn


bp = Blueprint("store", __name__)


def _get_cart() -> dict[str, int]:
    cart = session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
    # normalize quantities
    normalized: dict[str, int] = {}
    for k, v in cart.items():
        try:
            qty = int(v)
        except Exception:
            qty = 1
        normalized[str(k)] = max(1, qty)
    session["cart"] = normalized
    return normalized


def _set_cart(cart: dict[str, int]) -> None:
    session["cart"] = cart


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/products")
def products():
    items = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("products.html", products=items, format_ngn=format_ngn)


@bp.post("/cart/add/<int:product_id>")
def cart_add(product_id: int):
    cart = _get_cart()
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    _set_cart(cart)
    flash("Added to cart.")
    return redirect(url_for("store.products"))


@bp.post("/cart/remove/<int:product_id>")
def cart_remove(product_id: int):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    _set_cart(cart)
    return redirect(url_for("store.cart"))


@bp.post("/cart/update")
def cart_update():
    cart = _get_cart()
    for key in list(cart.keys()):
        form_key = f"qty_{key}"
        if form_key in request.form:
            try:
                cart[key] = max(1, int(request.form.get(form_key) or 1))
            except Exception:
                cart[key] = 1
    _set_cart(cart)
    return redirect(url_for("store.cart"))


@bp.get("/cart")
def cart():
    cart = _get_cart()

    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
    products_by_id = {p.id: p for p in products}

    lines = []
    total = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = products_by_id.get(pid)
        if not p:
            continue
        line_total = p.price_ngn * qty
        total += line_total
        lines.append({"product": p, "qty": qty, "line_total": line_total})

    return render_template("cart.html", lines=lines, total=total, format_ngn=format_ngn)


@bp.post("/checkout")
@login_required
def checkout_post():
    cart = _get_cart()
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for("store.products"))

    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    products_by_id = {p.id: p for p in products}

    order = Order(user_id=current_user.id, created_at=datetime.utcnow(), total_ngn=0)
    db.session.add(order)
    db.session.flush()  # assign order.id

    total = 0
    summary_lines = []

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = products_by_id.get(pid)
        if not p:
            continue
        qty = max(1, int(qty))

        item = OrderItem(
            order_id=order.id,
            product_id=p.id,
            quantity=qty,
            unit_price_ngn=p.price_ngn,
        )
        db.session.add(item)

        line_total = p.price_ngn * qty
        total += line_total
        summary_lines.append(f"- {p.name} x {qty} ({format_ngn(p.price_ngn)})")

    order.total_ngn = total

    initial_message = "Order placed:\n" + "\n".join(summary_lines) + f"\n\nTotal: {format_ngn(total)}"
    db.session.add(
        OrderMessage(order_id=order.id, sender_user_id=current_user.id, body=initial_message)
    )

    db.session.commit()

    # clear cart
    session["cart"] = {}

    return redirect(url_for("store.order_chat", order_id=order.id))


@bp.get("/orders")
@login_required
def my_orders():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders.html", orders=orders, format_ngn=format_ngn)


@bp.get("/orders/<int:order_id>/chat")
@login_required
def order_chat(order_id: int):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.")
        return redirect(url_for("store.products"))

    if not current_user.is_admin and order.user_id != current_user.id:
        flash("Not allowed.")
        return redirect(url_for("store.products"))

    messages = (
        OrderMessage.query.filter_by(order_id=order_id)
        .order_by(OrderMessage.created_at.asc())
        .all()
    )
    return render_template(
        "chat.html",
        order=order,
        messages=messages,
        format_ngn=format_ngn,
    )


@bp.post("/orders/<int:order_id>/chat")
@login_required
def order_chat_post(order_id: int):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.")
        return redirect(url_for("store.products"))

    if not current_user.is_admin and order.user_id != current_user.id:
        flash("Not allowed.")
        return redirect(url_for("store.products"))

    body = (request.form.get("message") or "").strip()
    if not body:
        return redirect(url_for("store.order_chat", order_id=order_id))

    sender_id = current_user.id
    db.session.add(OrderMessage(order_id=order_id, sender_user_id=sender_id, body=body))
    db.session.commit()

    return redirect(url_for("store.order_chat", order_id=order_id))
