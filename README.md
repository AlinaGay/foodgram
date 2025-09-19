# Foodgram

**Foodgram** is a platform for publishing, discovering, and storing culinary recipes.
Users can add their own dishes, save favorites, follow their favorite authors, and generate a shopping list based on ingredients.

---

## Demo Version

[https://foodgram-site.zapto.org](https://foodgram-site.zapto.org)

---

## Features

* **Registration and Authentication** (djoser + authtoken)
* **CRUD for Recipes** — create, edit, and delete recipes
* **Work with Ingredients and Tags** — filtering and search
* **Add Recipes to Favorites**
* **Generate and Download a Shopping List** based on ingredients
* **Follow Other Users** and their recipes
* **Upload/Change Avatar**
* **Filter by Tags, Authors, Favorites, and Cart**
* **Pagination** for all lists

---

## Technologies

* Python 3.11+
* Django 5.1
* Django REST Framework
* Django Filters
* Djoser (token-based authentication)
* PostgreSQL/SQLite
* Docker, docker-compose
* drf-yasg (auto-generated API documentation)

---

## Quick Start

### Clone the Repository

```bash
git clone https://github.com/yourusername/foodgram.git
cd foodgram
```

---

## Environment Setup

### Using Docker Compose (recommended)

1. Copy the `.env` file (see example below)

2. Start the project:

```bash
docker compose up -d
```

3. Run migrations:

```bash
docker compose exec backend python manage.py migrate
```

4. Populate ingredients:

```bash
docker compose exec backend python manage.py import_ingredients
```

5. Create a superuser:

```bash
docker compose exec backend python manage.py createsuperuser
```

6. Add tags via the admin panel (`/admin`) after logging in with the superuser credentials.

---

### Run Locally (without Docker)

1. Navigate to the project folder and create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations and collect static files:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

4. Populate ingredients:

```bash
python manage.py import_ingredients
```

5. Run the development server:

```bash
python manage.py runserver
```

6. Create a superuser:

```bash
python manage.py createsuperuser
```

7. Add tags via the admin panel (`/admin`) after logging in with the superuser credentials.

---

## Authentication

Uses **djoser + authtoken** (API tokens).
Authentication via email and password, token retrieval:

* `POST /api/auth/token/login/` — obtain a token (email, password)
* Add the token to the header: `Authorization: Token <your_token>`

---

## Author

[AlinaGay](https://github.com/AlinaGay)
| Backend Developer • Python Engineer |

