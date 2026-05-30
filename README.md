# Picura

Self-hosted photo and media library built with Django.

## Requirements

- Python 3.14+
- Node.js (for frontend assets)
- PostgreSQL

## Setup

### Database

Create a PostgreSQL user and database:

```bash
sudo -u postgres psql -c "CREATE USER picura WITH PASSWORD 'picura';"
sudo -u postgres psql -c "ALTER ROLE picura CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE picura OWNER picura;"
```

Then copy `.env.example` to `.env` and fill in your credentials (the defaults match the commands above).

For resetting the database:

```bash
sudo -u postgres psql -c "DROP DATABASE picura;"
sudo -u postgres psql -c "CREATE DATABASE picura OWNER picura;"
```

### Application

```bash
# Install Python dependencies
uv sync

# Install Node dependencies
npm install

# Build frontend assets
npm run build

# Apply database migrations
uv run manage.py migrate

# Start the development server
uv run manage.py runserver
```

## Development

Run tests:

```bash
uv run manage.py test
```

Build and watch frontend assets:

```bash
npm run dev
```

## Translations

```bash
# Extract/update translatable strings
uv run manage.py makemessages -a

# Compile translations
uv run manage.py compilemessages
```

Supported languages: German (`de`), English (`en`, source language).
