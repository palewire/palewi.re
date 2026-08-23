release: python manage.py migrate --noinput
web: gunicorn wsgi:application --log-file -
