# Procfile
release: python src/manage.py migrate --noinput && python src/manage.py collectstatic --noinput
web: gunicorn --chdir src dandd.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
