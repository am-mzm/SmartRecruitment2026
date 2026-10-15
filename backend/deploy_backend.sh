#!/usr/bin/env bash
set -Eeuo pipefail

BASE_DIR="/home/asandhu/SmartRecruitment2026/Pybackend-Final-2026"
COMPOSE_FILE="$BASE_DIR/docker-compose.yml"
SERVICE="pybackend"
CONTAINER="pybackend_revised"
IMAGE="pybackend_revised"
HEALTH_URL="http://localhost:8002/"
LOG_DIR="$BASE_DIR/deployment_logs"
SOURCE_BACKUP_DIR="/home/asandhu/SmartRecruitment2026/source_backups"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
CANDIDATE_TAG="candidate-${TIMESTAMP}"
ROLLBACK_TAG="rollback-${TIMESTAMP}"
CANDIDATE_IMAGE="${IMAGE}:${CANDIDATE_TAG}"
ROLLBACK_IMAGE="${IMAGE}:${ROLLBACK_TAG}"
LOG_FILE="$LOG_DIR/deploy_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

cd "$BASE_DIR"

echo "======================================================"
echo " SmartRecruitment Backend Deployment"
echo "======================================================"
echo "Time      : $(date)"
echo "Base      : $BASE_DIR"
echo "Candidate : $CANDIDATE_IMAGE"
echo "Rollback  : $ROLLBACK_IMAGE"
echo "Log       : $LOG_FILE"
echo

# ------------------------------------------------------
# 1. Required files
# ------------------------------------------------------
[[ -f "$BASE_DIR/Dockerfile" ]] || {
    echo "ERROR: Dockerfile not found."
    exit 1
}

[[ -f "$COMPOSE_FILE" ]] || {
    echo "ERROR: docker-compose.yml not found."
    exit 1
}

# ------------------------------------------------------
# 2. Compile critical Python files BEFORE build
# ------------------------------------------------------
echo "==> Compiling critical Python files..."

python3 -m py_compile \
    Searching_Top_CVs/vector_bm25_search_revised.py \
    Searching_Top_CVs/Process_Upload_Functions/upload_file_regex.py \
    Searching_Top_CVs/Process_Upload_Functions/employment_layout_engine_v1_CURRENT.py \
    Searching_Top_CVs/Process_Upload_Functions/employment_layout_ollama_validator_v1.py \
    app/server.py

echo "Python compile checks PASS."
echo

# ------------------------------------------------------
# 3. Backup source code BEFORE Docker cleanup/build
# ------------------------------------------------------
echo "==> Creating source-code safety backup..."

mkdir -p "$SOURCE_BACKUP_DIR"

SOURCE_BACKUP="$SOURCE_BACKUP_DIR/Pybackend-Final-2026_PRE_DEPLOY_${TIMESTAMP}.tar.gz"

tar     --exclude='./deployment_logs'     --exclude='./deploy_backend_PRE_AUTO_RETENTION_20261007.sh'     -czf "$SOURCE_BACKUP"     -C "$(dirname "$BASE_DIR")"     "$(basename "$BASE_DIR")"

if [[ ! -s "$SOURCE_BACKUP" ]]; then
    echo "ERROR: Source backup was not created successfully."
    exit 1
fi

echo "Source backup PASS:"
echo "  $SOURCE_BACKUP"
echo

# ------------------------------------------------------
# 4. Protect currently running production image
# ------------------------------------------------------
echo "==> Protecting current production image..."

CURRENT_IMAGE_ID="$(docker inspect "$CONTAINER" \
    --format '{{.Image}}' 2>/dev/null || true)"

if [[ -z "$CURRENT_IMAGE_ID" ]]; then
    echo "ERROR: Production container $CONTAINER is not available."
    exit 1
fi

docker tag "$CURRENT_IMAGE_ID" "$ROLLBACK_IMAGE"

echo "Rollback image created:"
echo "  $ROLLBACK_IMAGE"
echo "  $CURRENT_IMAGE_ID"
echo

# ------------------------------------------------------
# 4. Disk-space safety
# ------------------------------------------------------
free_gb() {
    df -Pk "$BASE_DIR" | awk 'NR==2 {printf "%d", $4/1024/1024}'
}

FREE_GB="$(free_gb)"
echo "==> Free disk before build: ${FREE_GB} GB"

if (( FREE_GB < 8 )); then
    echo "Free disk below 8 GB."
    echo "Safely clearing Docker BUILD CACHE only..."
    docker builder prune -af || true
    FREE_GB="$(free_gb)"
    echo "Free disk after build-cache cleanup: ${FREE_GB} GB"
fi

if (( FREE_GB < 5 )); then
    echo "ERROR: Less than 5 GB free after safe cleanup."
    echo "Deployment stopped BEFORE Docker build."
    echo "Production container, rollback images and ChromaDB were not changed."
    exit 1
fi

echo "Disk-space check PASS."
echo

# ------------------------------------------------------
# 5. Build a CANDIDATE image -- NEVER build to latest
# ------------------------------------------------------
echo "==> Building candidate image..."
echo "    $CANDIDATE_IMAGE"

if ! docker build \
    --progress=plain \
    -t "$CANDIDATE_IMAGE" \
    "$BASE_DIR"; then

    echo "ERROR: Candidate image build failed."
    echo "Production was NOT changed."
    echo "latest was NOT changed."

    docker image rm "$CANDIDATE_IMAGE" 2>/dev/null || true
    exit 1
fi

echo "Candidate build PASS."
echo

# ------------------------------------------------------
# 6. Validate candidate dependencies
# ------------------------------------------------------
echo "==> Validating candidate Python/ML dependencies..."

docker run --rm "$CANDIDATE_IMAGE" \
    python -c "import torch, sentence_transformers, transformers, chromadb, spacy, pymupdf, sklearn; assert not torch.cuda.is_available(); print('CANDIDATE_IMPORTS_PASS'); print('TORCH=', torch.__version__)"

echo "Candidate dependency validation PASS."
echo

# ------------------------------------------------------
# 7. Promote candidate to latest only after validation
# ------------------------------------------------------
echo "==> Promoting validated candidate to latest..."

docker tag "$CANDIDATE_IMAGE" "${IMAGE}:latest"

echo "latest now points to validated candidate."
echo

# ------------------------------------------------------
# 8. Recreate ONLY backend service
#    ChromaDB is intentionally untouched.
# ------------------------------------------------------
echo "==> Recreating backend service only..."

docker compose \
    -f "$COMPOSE_FILE" \
    up -d --no-build --force-recreate "$SERVICE"

echo

# ------------------------------------------------------
# 9. Production health check
# ------------------------------------------------------
echo "==> Waiting for production health..."

HEALTH_OK=0

for attempt in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
        HEALTH_OK=1
        echo "Production health PASS on attempt $attempt."
        break
    fi

    echo "Waiting for backend startup... ($attempt/30)"
    sleep 3
done

# ------------------------------------------------------
# 10. Automatic rollback on health failure
# ------------------------------------------------------
if (( HEALTH_OK == 0 )); then
    echo
    echo "ERROR: New production backend failed health check."
    echo "Starting automatic rollback..."

    docker tag "$ROLLBACK_IMAGE" "${IMAGE}:latest"

    docker compose \
        -f "$COMPOSE_FILE" \
        up -d --no-build --force-recreate "$SERVICE"

    echo "Waiting for rollback backend..."

    ROLLBACK_OK=0

    for attempt in $(seq 1 30); do
        if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
            ROLLBACK_OK=1
            echo "ROLLBACK HEALTH PASS."
            break
        fi

        sleep 3
    done

    if (( ROLLBACK_OK == 0 )); then
        echo "CRITICAL: Rollback backend also failed health check."
        echo "Inspect:"
        echo "  docker logs --tail 100 $CONTAINER"
        exit 2
    fi

    echo "Production restored to:"
    echo "  $ROLLBACK_IMAGE"
    exit 1
fi

# ------------------------------------------------------
# 11. Verify running image
# ------------------------------------------------------
RUNNING_IMAGE_ID="$(docker inspect "$CONTAINER" --format '{{.Image}}')"
LATEST_IMAGE_ID="$(docker image inspect "${IMAGE}:latest" --format '{{.Id}}')"

if [[ "$RUNNING_IMAGE_ID" != "$LATEST_IMAGE_ID" ]]; then
    echo "ERROR: Running container image does not match latest."
    echo "Running: $RUNNING_IMAGE_ID"
    echo "Latest : $LATEST_IMAGE_ID"
    exit 1
fi

# ------------------------------------------------------
# 12. Backend image retention
#     Keep ONLY:
#       1. Current production image
#       2. Immediately previous production image
#     ChromaDB images/containers/volumes are NEVER touched.
# ------------------------------------------------------
echo
echo "==> Cleaning obsolete backend image versions..."

NEW_IMAGE_ID="$RUNNING_IMAGE_ID"
PREVIOUS_IMAGE_ID="$CURRENT_IMAGE_ID"

echo "Protected current image : $NEW_IMAGE_ID"
echo "Protected previous image: $PREVIOUS_IMAGE_ID"

# Remove tags belonging to older pybackend_revised image generations.
while IFS= read -r OLD_IMAGE_ID; do
    [[ -z "$OLD_IMAGE_ID" ]] && continue

    FULL_IMAGE_ID="$(docker image inspect "$OLD_IMAGE_ID" --format '{{.Id}}' 2>/dev/null || true)"
    [[ -z "$FULL_IMAGE_ID" ]] && continue

    if [[ "$FULL_IMAGE_ID" != "$NEW_IMAGE_ID" && \
          "$FULL_IMAGE_ID" != "$PREVIOUS_IMAGE_ID" ]]; then

        echo "Removing obsolete backend image: $FULL_IMAGE_ID"
        docker image rm -f "$FULL_IMAGE_ID" 2>/dev/null || true
    fi
done < <(
    docker images "$IMAGE" \
        --format '{{.ID}}' |
    sort -u
)

# Remove obsolete tags from the PREVIOUS image.
# Keep only the rollback tag created by THIS deployment.
while IFS= read -r TAG; do
    [[ -z "$TAG" ]] && continue

    if [[ "$TAG" != "$ROLLBACK_IMAGE" ]]; then
        TAG_ID="$(docker image inspect "$TAG" --format '{{.Id}}' 2>/dev/null || true)"

        if [[ "$TAG_ID" == "$PREVIOUS_IMAGE_ID" ]]; then
            echo "Removing obsolete previous-image tag: $TAG"
            docker image rm "$TAG" 2>/dev/null || true
        fi
    fi
done < <(
    docker images "$IMAGE" \
        --format '{{.Repository}}:{{.Tag}}'
)

docker image prune -f >/dev/null 2>&1 || true

echo "Backend image retention PASS."
echo

# ------------------------------------------------------
# 13. Final status
# ------------------------------------------------------
echo
echo "======================================================"
echo " DEPLOYMENT SUCCESS"
echo "======================================================"

docker inspect "$CONTAINER" \
    --format 'Container={{.Name}} Image={{.Image}} Status={{.State.Status}}'

echo
echo "Health:"
curl -fsS "$HEALTH_URL"
echo

echo
echo "Images:"
docker images "$IMAGE" \
    --format "table {{.Tag}}\t{{.ID}}\t{{.Size}}" | head -12

echo
echo "Rollback preserved:"
echo "  $ROLLBACK_IMAGE"

echo
echo "Candidate preserved:"
echo "  $CANDIDATE_IMAGE"

echo
echo "ChromaDB was NOT recreated or modified by this deployment."
echo
echo "Deployment log:"
echo "  $LOG_FILE"
echo "======================================================"
