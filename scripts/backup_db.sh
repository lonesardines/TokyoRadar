#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

docker compose exec -T db pg_dump -U tokyoradar tokyoradar > "$BACKUP_DIR/tokyoradar_$TIMESTAMP.sql"

# Keep only last 7 backups
ls -t "$BACKUP_DIR"/tokyoradar_*.sql | tail -n +8 | xargs -r rm

echo "Backup saved: $BACKUP_DIR/tokyoradar_$TIMESTAMP.sql"
