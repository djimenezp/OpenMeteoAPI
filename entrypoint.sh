#!/bin/sh
set -e

# Directories (overrideable via env)
LOG_DIR="${LOG_DIR:-/app/log}"
DB_DIR="${DB_DIR:-/app/dbdata}"
STATIC_DIR="${DJANGO_STATIC_ROOT:-/app/staticfiles}"

# Create required dirs at runtime (works with volumes)
mkdir -p "$LOG_DIR" "$DB_DIR" "$STATIC_DIR" || true

# Cross-platform friendly permissions:
# - On Linux this ensures non-root processes can write.
# - On Windows/WSL2 mounted volumes can behave differently, but chmod won't break anything.
chmod -R a+rwx "$LOG_DIR" "$DB_DIR" "$STATIC_DIR" 2>/dev/null || true

exec "$@"
