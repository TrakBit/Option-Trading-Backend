release: python manage.py migrate
web: gunicorn upstox_server.wsgi --log-file -
worker: python worker.py
web: upstox_server.wsgi:application --port $PORT --bind 0.0.0.0 -v2
clock: python clock.py
chatworker: python manage.py clear_cache runworker --settings=upstox_server.settings -v2
