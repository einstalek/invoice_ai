# Inflow Backend

Django REST API for the Inflow invoice processing platform.

## Tech Stack

- **Django 5.2** + **Django REST Framework**
- **PostgreSQL** (SQLite fallback for local dev)
- **Celery + Redis** for async tasks (LLM extraction, ERP export)
- **SimpleJWT** for authentication
- **django-allauth** for Google OAuth
- **pdfplumber** for PDF text extraction
- **Replicate API** for LLM invoice field extraction
- **gspread + google-auth** for Google Sheets export via user OAuth

## Project Structure

```
backend/
├── config/          # Django settings, root URL config, WSGI/ASGI
├── accounts/        # User model, auth serializers, Google OAuth
├── organizations/   # Organization CRUD, memberships, invites, Google Sheets OAuth
├── invoices/        # Invoice upload, processing, review, approval, export
├── notifications/   # In-app notifications
├── manage.py
└── requirements.txt
```

## Prerequisites

- **Python 3.11+**
- **Redis** — required by Celery for async task processing (invoice extraction, ERP export)
- **PostgreSQL** — recommended for production; SQLite is used automatically if no `DB_NAME` / `DATABASE_URL` is set

### Installing Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl enable --now redis-server

# Verify
redis-cli ping  # should print PONG
```

### Installing PostgreSQL (optional for local dev)

SQLite works out of the box with no configuration. To use PostgreSQL instead:

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16
createdb inflow

# Ubuntu/Debian
sudo apt install postgresql
sudo -u postgres createdb inflow
```

## Setup

```bash
# Create and activate virtualenv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and configure
cp .env.example .env  # then fill in values (see table below)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start dev server
python manage.py runserver
```

## Running Services

You need **two** processes running during development:

### 1. Django dev server

```bash
python manage.py runserver
```

Runs on `http://localhost:8000` by default.

### 2. Celery worker (for async invoice processing)

```bash
celery -A config worker -l info
```

This requires Redis to be running. Celery handles:
- PDF text extraction + LLM field extraction after invoice upload
- Google Sheets export when booking an invoice

> **Tip:** Run each in a separate terminal, or use a process manager like `honcho` or `foreman`.

## Environment Variables

Create a `.env` file in the `backend/` directory. All variables have sensible defaults for local development — the only ones you **must** set for full functionality are marked with *.

### Core

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Django secret key. **Set in production.** |
| `DEBUG` | `True` | Debug mode. Set to `False` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Frontend origin(s), comma-separated |

### Database (optional for local dev)

If neither `DB_NAME` nor `DATABASE_URL` is set, SQLite is used automatically.

| Variable | Default | Description |
|---|---|---|
| `DB_NAME` | `inflow` | PostgreSQL database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |

### Celery / Redis

| Variable | Default | Description |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis URL for Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Redis URL for Celery results |

### Google OAuth *

Used for **both** Google login and Google Sheets integration. Get these from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Create an OAuth 2.0 Client ID (type: **Web application**)
2. Add `http://localhost:3000` to **Authorized JavaScript origins**
3. Add `http://localhost:3000` to **Authorized redirect URIs**
4. Enable the **Google Sheets API** and **Google Drive API** in [API Library](https://console.cloud.google.com/apis/library)

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_CLIENT_ID` * | (empty) | OAuth client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` * | (empty) | OAuth client secret from Google Cloud Console |

> **Note:** The same client ID/secret pair is used for user login (profile + email scopes) and for Google Sheets export (spreadsheets + drive.file scopes). The frontend requests different scopes for each flow.

### AWS S3 (optional — for invoice PDF storage)

If not set, PDFs are stored locally in `backend/media/`.

| Variable | Default | Description |
|---|---|---|
| `AWS_STORAGE_BUCKET_NAME` | (empty) | S3 bucket name — enables S3 storage when set |
| `AWS_ACCESS_KEY_ID` | (empty) | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | (empty) | AWS secret key |
| `AWS_S3_REGION_NAME` | `eu-central-1` | S3 region |
| `AWS_QUERYSTRING_EXPIRE` | `3600` | Presigned URL expiry in seconds |

### LLM (invoice extraction)

| Variable | Default | Description |
|---|---|---|
| `REPLICATE_API_TOKEN` * | (empty) | Replicate API token for LLM-powered extraction |
| `LLM_MODEL` | `qwen/qwen3-235b-a22b-instruct-2507` | Model identifier on Replicate |

### Example `.env` file

```env
# Required for full functionality
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxx
REPLICATE_API_TOKEN=r8_xxxxxx

# Optional — use PostgreSQL instead of SQLite
# DB_NAME=inflow
# DB_USER=postgres
# DB_PASSWORD=postgres

# Optional — use S3 instead of local file storage
# AWS_STORAGE_BUCKET_NAME=my-bucket
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=xxxx
```

## API Endpoints

| Prefix | Description |
|---|---|
| `api/auth/` | Login, logout, JWT refresh, Google OAuth login |
| `api/auth/registration/` | User registration |
| `api/auth/me/` | Current user profile, memberships, pending invites |
| `api/orgs/` | Organization CRUD |
| `api/orgs/<id>/members/` | Members, invites, accept/deactivate |
| `api/orgs/<id>/suppliers/` | Supplier CRUD |
| `api/orgs/<id>/invoices/` | Invoice upload, review, approval, export |
| `api/orgs/<id>/google-sheets/connect/` | Connect Google account for Sheets export |
| `api/orgs/<id>/google-sheets/disconnect/` | Disconnect Google Sheets |
| `api/notifications/` | User notifications |
| `admin/` | Django admin panel |

## Google Sheets Integration Flow

1. Organization owner selects "Google Sheets" as ERP type in settings
2. Clicks "Connect Google Account" — a Google OAuth popup requests Sheets + Drive scopes
3. Frontend sends the auth code to `POST /api/orgs/<id>/google-sheets/connect/`
4. Backend exchanges the code for access + refresh tokens and stores them in `erp_config`
5. Owner configures the target spreadsheet ID and worksheet name, then saves
6. When an approved invoice is booked, the Celery worker exports it to the Google Sheet
7. Token refresh is handled automatically — if the access token expires, the backend refreshes it using the stored refresh token
