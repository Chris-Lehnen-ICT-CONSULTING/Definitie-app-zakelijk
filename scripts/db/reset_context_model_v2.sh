#!/usr/bin/env bash
set -euo pipefail

DB_PATH="data/definities.db"
SCHEMA_PATH="src/database/schema.sql"

echo "🚨 Resetting database to Context Model V2 schema"
echo " - Removing $DB_PATH (if exists)"
rm -f "$DB_PATH" "$DB_PATH-shm" "$DB_PATH-wal" || true

echo " - Applying schema from $SCHEMA_PATH"
sqlite3 "$DB_PATH" < "$SCHEMA_PATH"

echo "✅ Database reset complete: $DB_PATH"
