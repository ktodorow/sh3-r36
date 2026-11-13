#!/bin/bash
# Saved native package installation, ABI closure and launcher diagnostic run.
set -euo pipefail
PORT_ROOT=$1
RUN_ID=$2
PAYLOAD=$3
RUN_DIR=$4
MODE=${5:-runtime}
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
MARKER='# SH3 project runtime diagnostics menu;'
if [ "$MODE" = gles ]; then
    MENU="$(dirname "$PORT_ROOT")/Silent Hill 3 Graphics Diagnostics.sh"
    MARKER='# SH3 project graphics diagnostics menu;'
fi
if [ "$MODE" = game ]; then
    MENU="$(dirname "$PORT_ROOT")/Silent Hill 3 Game.sh"
    MARKER='# SH3 project game menu;'
fi
if [ -e "$MENU" ] && ! grep -q "^$MARKER" "$MENU"; then
    echo 'Existing runtime menu not project-owned; preserved.' >&2; exit 3
fi
cp "$PAYLOAD/ports/$(basename "$MENU")" "$MENU"
chmod +x "$MENU"
if [ "$MODE" = game ]; then
    # Window-close probe; watchdog remains failure if game does not handle WM_QUIT.
    export SH3_SESSION_ISOLATED=1
    unset SH3_IMPORT_SESSION SH3_SEED_SESSION
    export SH3_KEYS='2:Return+0.4,5:Return+0.4,10:Return+0.4,15:Return+0.4,20:Return+0.4,25:Return+0.4,30:Return+0.4,35:Return+0.4,40:Return+0.4,45:Return+0.4,50:Return+0.4,55:Return+0.4,75:Escape+0.4,85:S+3,90:E+2'
    export SH3_INTERNAL_RESOLUTION=640x480
    export SH3_PEEK='72BFD0,72BFD4,72D2C0,8984E0,8984E8,898660,72C7F0,72C7F4,BCC630'
    source_launch=''
    for checkpoint in "$PORT_ROOT"/runs/*/session/savedata/data.001; do
        candidate="$(dirname "$(dirname "$(dirname "$checkpoint")")")"
        if [ -f "$checkpoint" ] && [ -f "$candidate/session/savedata/data.sys" ] &&
            [ -f "$candidate/exit-status.txt" ] && [ "$(cat "$candidate/exit-status.txt")" = 0 ]; then
            source_launch=$candidate
        fi
    done
    # Explicit unseeded scene starts fresh instead of inheriting latest owner save.
    if [ -f "$PAYLOAD/scene-plan.json" ] && [ ! -d "$PAYLOAD/scene-seed" ]; then
        source_launch=''
    fi
    if [ -f "$PAYLOAD/persistent-state" ]; then
        source_launch=''
        unset SH3_SESSION_ISOLATED SH3_INTERNAL_RESOLUTION
        if [ -d "$PAYLOAD/import-state" ]; then
            export SH3_IMPORT_SESSION="$PAYLOAD/import-state"
        fi
    fi
    source_session=${source_launch:+$source_launch/session}
    if [ -d "$PAYLOAD/scene-seed" ]; then
        source_session="$PAYLOAD/scene-seed"
        source_launch=deployed-scene-seed
    fi
    if [ -n "$source_session" ]; then
        export SH3_SEED_SESSION="$RUN_DIR/checkpoint-seed"
        mkdir -p "$SH3_SEED_SESSION/savedata"
        : > "$RUN_DIR/checkpoint-source.sha256"
        cache=cold
        for name in savedata/data.001 savedata/data.sys savedata/disp.ini savedata/key.ini; do
            if [ -f "$source_session/$name" ]; then
                sha256sum "$source_session/$name" >> "$RUN_DIR/checkpoint-source.sha256"
                cp -p "$source_session/$name" "$SH3_SEED_SESSION/$name"
            fi
        done
        if { [ -d "$PAYLOAD/scene-seed" ] || [ -f "$source_launch/checkpoint-replay.txt" ]; } &&
            [ -f "$source_session/sh3-progs.bin" ]; then
            sha256sum "$source_session/sh3-progs.bin" >> "$RUN_DIR/checkpoint-source.sha256"
            cp -p "$source_session/sh3-progs.bin" "$SH3_SEED_SESSION/sh3-progs.bin"
            cache=warm
        fi
        printf 'source_launch=%s\nprogram_cache=%s\ninternal_resolution=640x480\n' \
            "$(basename "$source_launch")" "$cache" > "$RUN_DIR/checkpoint-probe.txt"
        export SH3_KEYS='10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4,75:S+4'
    fi
    export SH3_STATS=1 SH3_GL_BACKEND=gles SH3_SHOW=1 SH3_QUIT_AFTER=100 SH3_MONITOR=1
    export SH3_SHOT_EVERY=60
    if [ -f "$PAYLOAD/scene-plan.json" ]; then
        cp "$PAYLOAD/scene-plan.json" "$RUN_DIR/scene-plan.json"
        python3 - "$RUN_DIR/scene-plan.json" > "$RUN_DIR/scene-values.txt" <<'PY'
import json, sys
plan = json.load(open(sys.argv[1]))
for key in ("keys", "seconds", "capture_every", "peek"):
    value = str(plan[key])
    if "\n" in value or "\r" in value:
        raise ValueError("Invalid scene value")
    print(value)
PY
        mapfile -t scene_values < "$RUN_DIR/scene-values.txt"
        export SH3_KEYS="${scene_values[0]}" SH3_QUIT_AFTER="${scene_values[1]}"
        export SH3_SHOT_EVERY="${scene_values[2]}" SH3_PEEK="${scene_values[3]}"
    fi
    printf 'keys=%s\nquit_after_seconds=%s\ncapture_every_frames=%s\ncontinuous_capture=0\n' \
        "$SH3_KEYS" "$SH3_QUIT_AFTER" "$SH3_SHOT_EVERY" > "$RUN_DIR/game-probe.txt"
    probe_limit=$((SH3_QUIT_AFTER + 45))
    if [ -f "$PAYLOAD/physical-controls" ]; then
        export SH3_PHYSICAL_CONTROLS=1
        probe_limit=1000
        printf 'scripted_input=0\ninput_log=1\nframe_capture=0\nperformance_sampler=0\nquit_after_seconds=900\n' \
            > "$RUN_DIR/game-probe.txt"
    fi
    if [ -f "$PAYLOAD/persistent-state" ]; then
        echo 'state_mode=persistent' >> "$RUN_DIR/game-probe.txt"
    else
        echo 'state_mode=isolated' >> "$RUN_DIR/game-probe.txt"
    fi
    # Sparse evidence, avoiding full framebuffer readback and SD write every frame.
    unset SH3_PRESENT_DUMP
    export SH3_SHOT="$PORT_ROOT/runs/${RUN_ID}-launch/shots"
    status=0
    timeout --kill-after=5s "${probe_limit}s" env SH3_PORT_ROOT="$PORT_ROOT" SH3_RUN_ID="${RUN_ID}-launch" SH3_SERVICE_WAIT=1 \
        SH3_PREFLIGHT_HEADLESS=1 bash "$MENU" || status=$?
    if [ -n "$source_launch" ]; then
        sha256sum -c "$RUN_DIR/checkpoint-source.sha256" > "$RUN_DIR/checkpoint-source-after.txt" || status=3
        if [ "$status" -eq 0 ]; then
            cp "$RUN_DIR/checkpoint-probe.txt" "$PORT_ROOT/runs/${RUN_ID}-launch/checkpoint-replay.txt"
        fi
    fi
    exit "$status"
fi
SH3_PORT_ROOT="$PORT_ROOT" SH3_RUN_ID="${RUN_ID}-launch" SH3_PREFLIGHT_HEADLESS=1 bash "$MENU"
