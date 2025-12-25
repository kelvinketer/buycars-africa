#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# --- DATABASE MIGRATIONS (CRITICAL UPDATE) ---
# Because we changed models.py (Added color, mileage, etc.),
# we must generate the migration files first.
python manage.py makemigrations
# Then we apply them to the database.
python manage.py migrate

# 2. Convert static files
python manage.py collectstatic --no-input

# 3. Auto-Create Admin User
python create_admin.py