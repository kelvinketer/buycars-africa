#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Convert static files (CSS/Images)
python manage.py collectstatic --no-input

# --- THE DANGER ZONE (Run Once) ---
# This wipes the cloud database completely so we can fix the migration conflict.
# MAKE SURE 'nuke_db.py' EXISTS BEFORE PUSHING!
python nuke_db.py
# ----------------------------------

# 3. Apply database migrations (Re-creates clean tables)
python manage.py migrate

# 4. Auto-Create Admin User
python create_admin.py