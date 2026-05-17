# Curio

A media library built with Django.

## Tech stack

- [Django](https://www.djangoproject.com/) — backend framework
- [Alpine.js](https://alpinejs.dev/) — frontend interactivity
- [Vite](https://vite.dev/) — frontend asset bundling
- [Lucide](https://lucide.dev/) — icons (inline SVG partials in `curio/core/templates/icons/`)

## Requirements

- Python 3.14+
- Node.js (for frontend assets)
- PostgreSQL

## Setup

### Database

Create a PostgreSQL user and database:

```bash
sudo -u postgres psql -c "CREATE USER curio WITH PASSWORD 'curio';"
sudo -u postgres psql -c "ALTER ROLE curio CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE curio OWNER curio;"
```

Then copy `.env.example` to `.env` and fill in your credentials (the defaults match the commands above).

For resetting the database:

```bash
sudo -u postgres psql -c "DROP DATABASE curio;"
sudo -u postgres psql -c "CREATE DATABASE curio OWNER curio;"
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
