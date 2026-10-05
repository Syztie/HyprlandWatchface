#!/usr/bin/env bash
# Builds the official WFF XML validator and memory footprint evaluator from
# github.com/google/watchface (pinned commit) into tools/bin/.
set -euo pipefail

WATCHFACE_COMMIT=b6cdda0acd3e4c5d0be5624fcdc01209380029d1
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HERE/bin"
SRC="$BIN/watchface"

mkdir -p "$BIN"
if [ ! -d "$SRC/.git" ]; then
    git clone --quiet https://github.com/google/watchface.git "$SRC"
fi
git -C "$SRC" fetch --quiet --depth 1 origin "$WATCHFACE_COMMIT" 2>/dev/null || true
git -C "$SRC" checkout --quiet "$WATCHFACE_COMMIT"

if [ ! -f "$BIN/wff-validator.jar" ]; then
    (cd "$SRC/third_party/wff" && ./gradlew --quiet :specification:validator:executable-jar)
    cp "$SRC/third_party/wff/specification/validator/build/libs/wff-validator.jar" "$BIN/"
fi
if [ ! -f "$BIN/memory-footprint.jar" ]; then
    (cd "$SRC/play-validations" && ./gradlew --quiet :memory-footprint:executable-jar)
    cp "$SRC/play-validations/memory-footprint/build/libs/memory-footprint.jar" "$BIN/"
fi
ls -1 "$BIN"/*.jar
