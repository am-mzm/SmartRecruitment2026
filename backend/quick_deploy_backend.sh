#!/usr/bin/env bash
set -Eeuo pipefail

BASE_DIR="/home/asandhu/SmartRecruitment2026/Pybackend-Final-2026"
CONTAINER="pybackend_revised"
CONTAINER_ROOT="/pybackend_revised"
HEALTH_URL="http://localhost:8002/"
BACKUP_ROOT="/home/asandhu/SmartRecruitment2026/quick_deploy_backups"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

cd "$BASE_DIR"

if (( $# == 0 )); then
    echo "Usage:"
    echo "  ./quick_deploy_backend.sh <relative-python-file> [more-files...]"
    echo
    echo "Example:"
    echo "  ./quick_deploy_backend.sh Searching_Top_CVs/Process_Upload_Functions/upload_file_regex.py"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "======================================================"
echo " SmartRecruitment QUICK Backend Deployment"
echo "======================================================"
echo "Time   : $(date)"
echo "Backup : $BACKUP_DIR"
echo

FILES=("$@")

# ------------------------------------------------------
# 1. Validate and compile source files
# ------------------------------------------------------
echo "==> Validating source files..."

for FILE in "${FILES[@]}"; do
    if [[ "$FILE" = /* ]] || [[ "$FILE" == *".."* ]]; then
        echo "ERROR: Only safe relative paths under $BASE_DIR are allowed:"
        echo "  $FILE"
        exit 1
    fi

    if [[ ! -f "$BASE_DIR/$FILE" ]]; then
        echo "ERROR: File not found:"
        echo "  $BASE_DIR/$FILE"
        exit 1
    fi

    if [[ "$FILE" != *.py ]]; then
        echo "ERROR: Quick deploy accepts Python (.py) files only:"
        echo "  $FILE"
        exit 1
    fi

    python3 -m py_compile "$BASE_DIR/$FILE"
    echo "  COMPILE PASS: $FILE"
done

# ------------------------------------------------------
# 2. Verify backend container
# ------------------------------------------------------
if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "ERROR: Container $CONTAINER does not exist."
    exit 1
fi

if [[ "$(docker inspect "$CONTAINER" --format '{{.State.Running}}')" != "true" ]]; then
    echo "ERROR: Container $CONTAINER is not running."
    exit 1
fi

# ------------------------------------------------------
# 3. Backup CURRENT container files
# ------------------------------------------------------
echo
echo "==> Backing up current production container files..."

for FILE in "${FILES[@]}"; do
    mkdir -p "$BACKUP_DIR/$(dirname "$FILE")"

    docker cp \
        "$CONTAINER:$CONTAINER_ROOT/$FILE" \
        "$BACKUP_DIR/$FILE"

    echo "  BACKUP: $FILE"
done

# ------------------------------------------------------
# Rollback function
# ------------------------------------------------------
rollback() {
    echo
    echo "==> QUICK DEPLOY FAILED - restoring previous files..."

    for FILE in "${FILES[@]}"; do
        docker cp \
            "$BACKUP_DIR/$FILE" \
            "$CONTAINER:$CONTAINER_ROOT/$FILE"
    done

    docker restart "$CONTAINER" >/dev/null

    echo "Waiting for rollback health..."

    for attempt in $(seq 1 30); do
        if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
            echo "ROLLBACK HEALTH PASS."
            echo "Previous production files restored."
            exit 1
        fi
        sleep 2
    done

    echo "CRITICAL: Rollback health check failed."
    echo "Inspect:"
    echo "  docker logs --tail 100 $CONTAINER"
    exit 2
}

# ------------------------------------------------------
# 4. Copy new files into running container
# ------------------------------------------------------
echo
echo "==> Installing new Python files..."

for FILE in "${FILES[@]}"; do
    docker cp \
        "$BASE_DIR/$FILE" \
        "$CONTAINER:$CONTAINER_ROOT/$FILE"

    echo "  INSTALLED: $FILE"
done

# ------------------------------------------------------
# 5. Compile INSIDE production container
# ------------------------------------------------------
echo
echo "==> Compiling inside container..."

for FILE in "${FILES[@]}"; do
    if ! docker exec "$CONTAINER" \
        python -m py_compile "$CONTAINER_ROOT/$FILE"; then
        rollback
    fi
done

echo "Container compile PASS."

# ------------------------------------------------------
# 6. Restart backend
# ------------------------------------------------------
echo
echo "==> Restarting backend..."

if ! docker restart "$CONTAINER" >/dev/null; then
    rollback
fi

# ------------------------------------------------------
# 7. Health check
# ------------------------------------------------------
echo "==> Waiting for backend health..."

HEALTH_OK=0

for attempt in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
        HEALTH_OK=1
        echo "Health PASS on attempt $attempt."
        break
    fi

    sleep 2
done

if (( HEALTH_OK == 0 )); then
    rollback
fi

echo
echo "======================================================"
echo " QUICK DEPLOYMENT SUCCESS"
echo "======================================================"
echo "Files:"
printf '  %s\n' "${FILES[@]}"
echo
echo "Health:"
curl -fsS "$HEALTH_URL"
echo
echo
echo "Backup:"
echo "  $BACKUP_DIR"
echo
echo "Docker image was NOT rebuilt."
echo "ChromaDB was NOT modified."
echo
echo "IMPORTANT:"
echo "Quick-deployed files exist only in the running container."
echo "Run ./deploy_backend.sh later to bake stable source into an image."
echo "======================================================"
