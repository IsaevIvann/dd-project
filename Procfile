# Procfile
release: cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: cd src && gunicorn dandd.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
