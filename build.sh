#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Convert static files
python manage.py collectstatic --no-input

# 3. Apply database migrations
# Since you are on SQLite, this creates a fresh DB every time automatically!
python manage.py migrate

# 4. Auto-Create Admin User
python create_admin.py