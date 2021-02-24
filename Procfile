release: |
  python manage.py compilescss;
  python manage.py collectstatic --noinput;
  python manage.py migrate;
web: gunicorn wsgi:application --log-file -
