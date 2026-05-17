# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Use `uv run` to execute management commands (Python 3.14, managed via `.python-version`):

```bash
uv run manage.py runserver
uv run pytest                                  # all tests
uv run pytest curio/my_account/                # single app
uv run manage.py migrate
uv run manage.py makemessages -l de -l en      # extract translatable strings (first run)
uv run manage.py makemessages -a               # update existing .po files
uv run manage.py compilemessages               # compile .po → .mo
```

## Code style

Use single-quote string literals in Python.

**CSS:** Follow the [CUBE CSS](https://cube.fyi/) methodology — Compositions, Utilities, Blocks, Exceptions.

## Testing

TDD is preferred. Write tests before or alongside implementation. Use `uv run pytest` — not `manage.py test`.

## Git

Keep commit messages short (one line is usually enough). Do not add `Co-Authored-By` trailers.

`.mo` files are gitignored — never stage or commit them.

## Architecture

**Project layout:** The Django project package is `curio/` (contains `settings.py`, `urls.py`). Apps live inside it as sub-packages (e.g. `curio/my_account/`).

**Custom user model:** `my_account.User` extends `AbstractUser` and is set as `AUTH_USER_MODEL`. All user references must use `get_user_model()` or `settings.AUTH_USER_MODEL`, not `auth.User` directly.

**i18n:** `LocaleMiddleware` is active. Supported languages are `de` and `en` (default). Translation files live in `locale/` at the project root. Only German needs `.po` entries — English is the source language and has no `.po` file.

**Dependencies** (see `pyproject.toml`): Django 6, `django-allauth` (installed but not yet wired into `INSTALLED_APPS`), `psycopg` (PostgreSQL is used in development).

**Models:** Every model must include `created_at = models.DateTimeField(auto_now_add=True)` and `updated_at = models.DateTimeField(auto_now=True)`.
