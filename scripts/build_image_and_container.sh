#!/bin/sh

set -e

if [ -z "$1" ]; then
  echo "Error: Image name is required."
  echo "Usage: $0 <image_name> [secret_key] [jwt_secret] [database_url]"
  exit 1
fi

IMAGE_NAME="$1"
PORT=5000

# Optional variables: fallback to existing shell env vars, or built-in defaults
SECRET_KEY="${2:-${SECRET_KEY:-secret}}"
JWT_SECRET_KEY="${3:-${JWT_SECRET_KEY:-secret}}"
DATABASE_URL="${4:-${DATABASE_URL:-sqlite:///:memory:}}"

docker build -t "$IMAGE_NAME" .

docker run -d \
  --rm \
  -p "$PORT:$PORT" \
  -e SECRET_KEY="$SECRET_KEY" \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e DATABASE_URL="$DATABASE_URL" \
  "$IMAGE_NAME"