#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/settings/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() { echo -e "${GREEN}[step]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# ── Step 1: Validate environment variables ────────────────────────────────────
step "1. Validating environment variables..."
if [ ! -f "$ENV_FILE" ]; then
    fail "Missing $ENV_FILE — copy settings/.env.example to settings/.env and fill in values."
fi

REQUIRED_VARS=(
    BLOG_ENV_ID
    BLOG_SECRET_KEY
    BLOG_DEBUG
    BLOG_ALLOWED_HOSTS
    BLOG_REDIS_URL
    BLOG_EMAIL_BACKEND
    BLOG_DEFAULT_FROM_EMAIL
)

for var in "${REQUIRED_VARS[@]}"; do
    value=$(grep -E "^${var}=" "$ENV_FILE" | cut -d'=' -f2- | tr -d ' ')
    if [ -z "$value" ]; then
        fail "Required environment variable '$var' is missing or blank in $ENV_FILE"
    fi
done
echo "  All required environment variables are present."

# ── Step 2: Create virtual environment and install dependencies ───────────────
step "2. Creating virtual environment and installing dependencies..."
cd "$PROJECT_DIR"
if [ ! -d "env" ]; then
    python3 -m venv env || fail "Failed to create virtual environment"
fi
env/bin/pip install -r requirements/dev.txt -q || fail "Failed to install dependencies"
echo "  Dependencies installed."

# ── Step 3: Run migrations ────────────────────────────────────────────────────
step "3. Running migrations..."
env/bin/python manage.py migrate --no-input || fail "Failed to run migrations"
echo "  Migrations applied."

# ── Step 4: Collect static files ─────────────────────────────────────────────
step "4. Collecting static files..."
env/bin/python manage.py collectstatic --no-input -v 0 || fail "Failed to collect static files"
echo "  Static files collected."

# ── Step 5: Compile translation files ────────────────────────────────────────
step "5. Compiling translation files..."
env/bin/python manage.py compilemessages --locale ru --locale kk --locale en -v 0 2>/dev/null || \
    warn "compilemessages returned non-zero (msgfmt may not be installed)"
echo "  Translation files compiled."

# ── Step 6: Create superuser ──────────────────────────────────────────────────
step "6. Creating superuser..."
SUPERUSER_EMAIL="admin@blogapi.com"
SUPERUSER_PASSWORD="Admin1234!"
env/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD',
        first_name='Admin',
        last_name='User',
    )
    print('  Superuser created.')
else:
    print('  Superuser already exists, skipping.')
" || fail "Failed to create superuser"

# ── Step 7: Seed database ─────────────────────────────────────────────────────
step "7. Seeding database with test data..."
env/bin/python manage.py seed_data || fail "Failed to seed database"

# ── Step 8: Start development server ─────────────────────────────────────────
step "8. Starting development server..."
echo ""
echo "========================================"
echo "  Blog API is ready!"
echo "========================================"
echo "  API:         http://127.0.0.1:8000/api/"
echo "  Swagger UI:  http://127.0.0.1:8000/api/docs/"
echo "  ReDoc:       http://127.0.0.1:8000/api/redoc/"
echo "  Admin:       http://127.0.0.1:8000/admin/"
echo ""
echo "  Superuser credentials:"
echo "    Email:    $SUPERUSER_EMAIL"
echo "    Password: $SUPERUSER_PASSWORD"
echo ""
echo "  Test users (password: testpass123):"
echo "    alice@example.com (en)"
echo "    bob@example.com   (ru)"
echo "    carol@example.com (kk)"
echo "========================================"
echo ""

env/bin/python manage.py runserver
