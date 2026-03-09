#/bin/bash
rm db.sqlite3
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=sandals-sick-there
python manage.py createsuperuser --noinput --username="admin" --email="admin@example.com" || true
