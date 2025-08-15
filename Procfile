web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && (python manage.py createsuperuser --noinput || true) && gunicorn dandd.wsgi:application --bind 0.0.0.0:${PORT}




