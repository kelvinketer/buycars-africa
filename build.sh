#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Convert static files (CSS/Images)
python manage.py collectstatic --no-input

# 3. Apply database migrations
python manage.py migrate

# 4. Auto-Create Admin User (The "Backdoor" Fix)
python create_admin.py