#!/usr/bin/env bash
set -euo pipefail

# cleanup_assets.sh
# Removes generated notification QR assets and related PDFs from the repo.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Remove QR assets
if [ -d "assets/qr-codes" ]; then
  rm -rf "assets/qr-codes"
fi

# Remove archive zip
if [ -f "assets/sgnia-notification-qr-codes.zip" ]; then
  rm -f "assets/sgnia-notification-qr-codes.zip"
fi

# Remove notification PDFs if they are kept as local files under the repo
find . -type f \( \
  -iname "*.pdf" -o \
  -iname "*.png" \
\) -path "./assets/*" -delete 2>/dev/null || true

# Optional: remove any manually generated notification PDF folder if used
if [ -d "notifications" ]; then
  rm -rf "notifications"
fi

# Optional: remove any exported QR folder if used
if [ -d "qr" ]; then
  rm -rf "qr"
fi

echo "Notification QR/PDF asset cleanup complete."
