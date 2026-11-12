#!/bin/bash
# Saved native package installation, ABI closure and launcher diagnostic run.
set -euo pipefail
PORT_ROOT=$1
RUN_ID=$2
PAYLOAD=$3
RUN_DIR=$4
if pgrep -x sh3 >/dev/null; then echo 'Existing sh3 process present; preserved.' >&2; exit 3; fi
if [ -e "$PORT_ROOT/runtime" ] && [ ! -f "$PORT_ROOT/runtime/.sh3-runtime-owned" ]; then
    echo 'Existing runtime not project-owned; preserved.' >&2; exit 3
fi
mkdir -p "$PORT_ROOT/runtime"
(cd "$PAYLOAD/runtime" && sha256sum -c artifacts.sha256) > "$RUN_DIR/package-integrity.txt"
# Preserve every original binary in its run payload; install only explicit native package files.
cp "$PAYLOAD/runtime/"* "$PORT_ROOT/runtime/"
chmod +x "$PORT_ROOT/runtime/sh3"
touch "$PORT_ROOT/runtime/.sh3-runtime-owned"
sha256sum "$PORT_ROOT/runtime/sh3" > "$RUN_DIR/runtime.sha256"
readelf -h -l -d -V "$PORT_ROOT/runtime/sh3" > "$RUN_DIR/runtime-elf.txt"
ldd "$PORT_ROOT/runtime/sh3" > "$RUN_DIR/runtime-dependencies.txt" 2> "$RUN_DIR/runtime-dependencies.stderr.txt"
if grep -q 'not found' "$RUN_DIR/runtime-dependencies.txt"; then
    echo 'Unresolved runtime dependency; see closure evidence.' >&2; exit 3
fi
awk '/=> \// {print $3} /^[[:space:]]*\// {print $1}' "$RUN_DIR/runtime-dependencies.txt" | sort -u |
while IFS= read -r library; do
    printf '\n[library %s]\n' "$library"
    readlink -f "$library"
    file -L "$library"
    sha256sum "$library"
    readelf -h -d -V "$library"
done > "$RUN_DIR/runtime-closure.txt" 2> "$RUN_DIR/runtime-closure.stderr.txt"
MENU="$(dirname "$PORT_ROOT")/Silent Hill 3 Runtime Diagnostics.sh"
if [ -e "$MENU" ] && ! grep -q '^# SH3 project runtime diagnostics menu;' "$MENU"; then
    echo 'Existing runtime menu not project-owned; preserved.' >&2; exit 3
fi
cp "$PAYLOAD/ports/Silent Hill 3 Runtime Diagnostics.sh" "$MENU"
chmod +x "$MENU"
SH3_PORT_ROOT="$PORT_ROOT" SH3_RUN_ID="${RUN_ID}-launch" SH3_PREFLIGHT_HEADLESS=1 bash "$MENU"
