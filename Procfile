web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn dandd.wsgi:application --bind 0.0.0.0:${PORT}
