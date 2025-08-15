release: python src/manage.py migrate --noinput && python src/manage.py collectstatic --noinput
web: gunicorn dandd.wsgi:application --bind 0.0.0.0:$PORT
