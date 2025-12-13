# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project type
This repo is a small Flask + MariaDB storefront.
- Backend: Flask (server-rendered Jinja templates)
- DB: MariaDB (via SQLAlchemy + PyMySQL)
- Frontend: plain HTML/CSS (no React)

## Common commands
### Setup (first time)
Create a venv and install dependencies:
- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`

Create your `.env`:
- `cp .env.example .env`
- Edit `DATABASE_URL` to point at your local MariaDB instance.

Initialize DB tables:
- `flask --app app.py init-db`

### Run (dev)
- `flask --app app.py run --debug`
- Open `http://127.0.0.1:5000/`

### “Build”, “lint”, and “test”
- Build: none.
- Lint: none configured.
- Tests: none configured.

## High-level architecture
### Entry points
- `app.py`
  - Flask entrypoint (`create_app()` factory in `app/__init__.py`).

### Backend modules
- `app/__init__.py`
  - App factory, config loading from `.env`, extension setup, blueprint registration.
  - Defines a `flask init-db` CLI command (uses `db.create_all()`).

- `app/models.py`
  - Core DB models:
    - `User` (auth + `is_admin`)
    - `Product` (name/description/price/image_path)
    - `Order` + `OrderItem`
    - `OrderMessage` (simple per-order chat thread)
  - `format_ngn()` helper for NGN display.

- `app/auth_routes.py`
  - `/register`, `/login`, `/logout`
  - `/admin-claim` (insecure-by-design admin enable flow; accessed via a hidden link on the login page).

- `app/store_routes.py`
  - `/` landing page
  - `/products` (DB-driven catalog)
  - `/cart` + `POST /cart/add/<id>` / `POST /cart/update` / `POST /cart/remove/<id>`
  - `POST /checkout` creates an `Order` in the DB and starts the in-app chat thread.
  - `/orders` and `/orders/<id>/chat` (customer chat with admin for a given order)

- `app/admin_routes.py`
  - `/admin/*` routes (admin-only)
  - Product management (add via image upload from phone, delete)
  - User list + promote/demote other users to admin
  - Orders list showing who ordered what, with links into the chat thread

### Templates and static assets
- Templates are in `templates/` (Jinja).
- Static assets are in `static/`:
  - `static/css/*`
  - `static/images/*` (legacy sample images)
  - `static/uploads/*` (admin-uploaded product images; default is gitignored)

### State / data flow
- Cart is stored server-side in the Flask session (`session["cart"]` mapping `{product_id: quantity}`).
- Checkout creates an `Order` + `OrderItem` rows, then redirects the user to the in-app chat for that order.
