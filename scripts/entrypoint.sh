#!/bin/sh
set -e

echo "Waiting for Redis..."
until python3 -c "import redis; r = redis.from_url('$BLOG_REDIS_URL'); r.ping()" 2>/dev/null; do
    echo "  Redis not ready, retrying in 2s..."
    sleep 2
done
echo "Redis is up."

echo "Running migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input -v 0

echo "Compiling messages..."
python manage.py compilemessages --locale ru --locale kk --locale en -v 0 2>/dev/null || echo "compilemessages skipped (msgfmt not available)"

if [ "$BLOG_SEED_DB" = "true" ]; then
    echo "Seeding database..."
    python manage.py seed
fi

echo "Starting: $@"
exec "$@"