web: gunicorn woo_pim.wsgi --log-file - --timeout 120
release: npm install && npm run build:css && python manage.py collectstatic --noinput