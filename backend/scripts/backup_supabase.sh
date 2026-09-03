#!/usr/bin/env bash
# ==============================================================================
# Supabase / PostgreSQL Snapshot Backup Script (Bash)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${BACKEND_DIR}/backups"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BACKUP_FILE="${BACKUP_DIR}/supabase_backup_${TIMESTAMP}.sql"

# Load environment variables from .env if present
ENV_FILE="${BACKEND_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    echo "[INFO] Loading environment variables from ${ENV_FILE}..."
    export $(grep -v '^#' "$ENV_FILE" | grep -E '^(DB_URL|DATABASE_URL)=' | xargs -0) || true
fi

TARGET_URL="${DB_URL:-${DATABASE_URL:-}}"

if [ -z "$TARGET_URL" ]; then
    echo "[ERROR] Neither DB_URL nor DATABASE_URL is set."
    echo "Please define DB_URL in backend/.env or as an environment variable."
    exit 1
fi

# Convert asyncpg/postgresql+asyncpg URI to standard postgresql:// for pg_dump if needed
CLEAN_URL=$(echo "$TARGET_URL" | sed 's/postgresql+asyncpg:\/\//postgresql:\/\//')

mkdir -p "$BACKUP_DIR"

echo "[INFO] Starting database backup at $(date)..."
echo "[INFO] Destination: ${BACKUP_FILE}"

if command -v pg_dump &> /dev/null; then
    pg_dump "$CLEAN_URL" \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        --file="$BACKUP_FILE"
    
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[SUCCESS] Backup completed successfully!"
    echo "[INFO] Backup size: ${FILE_SIZE}"
    echo "[INFO] Location: ${BACKUP_FILE}"
else
    echo "[ERROR] pg_dump utility not found in PATH."
    echo "Please install PostgreSQL client tools or add pg_dump to PATH."
    exit 1
fi
