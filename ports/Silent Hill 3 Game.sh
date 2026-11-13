#!/bin/bash
# SH3 project game menu; native Linux ARM64, session-owned writable state.
export SH3_MODE=game
export SH3_STATS=${SH3_STATS:-1}
export SH3_PORT_ROOT=${SH3_PORT_ROOT:-"$(cd "$(dirname "$0")" && pwd)/sh3"}
export SH3_RUN_ID=${SH3_RUN_ID:-"$(date -u +%Y%m%dT%H%M%SZ)-$$"}
case "$SH3_RUN_ID" in ''|*[!A-Za-z0-9_-]*) echo 'Invalid run ID' >&2; exit 3 ;; esac
SERVICE_DIR="$SH3_PORT_ROOT/runs/${SH3_RUN_ID}-service"
mkdir -p "$SH3_PORT_ROOT/runs" || exit 3
mkdir "$SERVICE_DIR" || { echo 'Service run already exists; preserving evidence.' >&2; exit 3; }
run_limits=()
if [ "${SH3_PHYSICAL_CONTROLS:-0}" = 1 ]; then
    export SH3_INPUT_LOG=1 SH3_GL_BACKEND=gles SH3_SHOW=1 SH3_QUIT_AFTER=900
    unset SH3_STATS SH3_KEYS SH3_PEEK SH3_SHOT SH3_SHOT_EVERY SH3_PRESENT_DUMP SH3_MONITOR
    # Bound an unattended launcher screen too; game deadline alone starts after Play.
    run_limits=(--property=RuntimeMaxSec=930)
    printf 'scripted_input=0\ninput_log=1\nframe_capture=0\nperformance_sampler=0\nquit_after_seconds=900\n' \
        > "$SERVICE_DIR/physical-controls.txt"
fi
privilege=()
if [ "$(id -u)" -ne 0 ]; then privilege=(sudo -n); fi
environment=()
for name in HOME USER LOGNAME SHELL PATH LANG TERM XDG_DATA_HOME XDG_RUNTIME_DIR \
    DBUS_SESSION_BUS_ADDRESS SDL_GAMECONTROLLERCONFIG_FILE DEVICE param_device HOTKEY \
    ANALOGSTICKS SDL_KMSDRM_DEVICE_INDEX SDL_KMSDRM_ORIENTATION SDL_KMSDRM_ROTATION \
    SH3_PORT_ROOT SH3_RUN_ID SH3_MODE SH3_DATA_DIR SH3_PACKAGE_DIR SH3_PREFLIGHT_HEADLESS \
    SH3_KEYS SH3_STATS SH3_GL_BACKEND SH3_SHOW SH3_QUIT_AFTER SH3_PRESENT_DUMP \
    SH3_SEED_SESSION SH3_INTERNAL_RESOLUTION SH3_PEEK SH3_INPUT_LOG \
    SH3_SHOT SH3_SHOT_EVERY SH3_MONITOR; do
    if [ "${!name+x}" ]; then environment+=("--setenv=$name=${!name}"); fi
done
wait_options=()
if [ "${SH3_SERVICE_WAIT:-0}" = 1 ]; then wait_options=(--wait); fi
# Separate service survives frontend's KillMode=control-group; fixed unit prevents doubles.
"${privilege[@]}" systemd-run --unit=sh3-r36s-game --collect --property=Type=exec \
    --uid="$(id -u)" --gid="$(id -g)" --property="SupplementaryGroups=$(id -Gn)" \
    --property=KillMode=control-group --property=TimeoutStopSec=40 \
    --property="StandardOutput=append:$SERVICE_DIR/stdout.txt" \
    --property="StandardError=append:$SERVICE_DIR/stderr.txt" \
    --property="ExecStopPost=+/bin/bash \"$SH3_PORT_ROOT/preflight/ports/restore-frontend.sh\" \"$SH3_PORT_ROOT\" \"$SH3_RUN_ID\"" \
    "${wait_options[@]}" "${run_limits[@]}" "${environment[@]}" \
    /bin/bash "$SH3_PORT_ROOT/preflight/ports/game-session.sh"
exit $?
