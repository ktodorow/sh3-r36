#!/bin/bash
# SH3 project preflight launcher; optional native runtime diagnostics.
PORT_ROOT=${SH3_PORT_ROOT:-"$(cd "$(dirname "$0")" && pwd)/sh3"}
DATA_DIR=${SH3_DATA_DIR:-"$PORT_ROOT/gamedata"}
RUN_ID=${SH3_RUN_ID:-"$(date -u +%Y%m%dT%H%M%SZ)-$$"}
case "$RUN_ID" in ''|*[!A-Za-z0-9_-]*) echo 'Invalid run ID' >&2; exit 3 ;; esac
RUN_DIR="$PORT_ROOT/runs/$RUN_ID"
mkdir -p "$PORT_ROOT/runs" || exit 3
mkdir "$RUN_DIR" || { echo 'Run already exists or is unwritable; preserving evidence.' >&2; exit 3; }
printf '%s\n' "$RUN_ID" > "$RUN_DIR/run-id.txt"
main() {
    XDG_DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
    unset controlfolder
    for candidate in /opt/system/Tools/PortMaster /opt/tools/PortMaster \
        "$XDG_DATA_HOME/PortMaster" /roms2/ports/PortMaster /roms/ports/PortMaster; do
        if [ -f "$candidate/control.txt" ]; then
            controlfolder=$candidate
            break
        fi
    done
    if [ -z "${controlfolder:-}" ]; then
        echo 'PortMaster control.txt missing; install/configure PortMaster before preflight.' >&2
        exit 3
    fi
    cleanup() {
        local status=$?
        trap - EXIT
        # Preflight starts no input helper; PortMaster's broad pkill owns none here.
        pm_gptokeyb_finish() { :; }
        if declare -F pm_finish >/dev/null; then pm_finish; fi
        exit "$status"
    }
    trap cleanup EXIT
    source "$controlfolder/control.txt"
    local helper_status=$?
    trap cleanup EXIT
    if [ "$helper_status" -ne 0 ]; then
        echo 'PortMaster control.txt failed; data validation not attempted.' >&2
        exit 3
    fi
    if [ -f "$controlfolder/mod_${CFW_NAME}.txt" ]; then
        source "$controlfolder/mod_${CFW_NAME}.txt"
        helper_status=$?
        trap cleanup EXIT
        if [ "$helper_status" -ne 0 ]; then
            echo 'PortMaster firmware helper failed; data validation not attempted.' >&2
            exit 3
        fi
    fi
    if ! get_controls; then
        echo 'PortMaster controls failed; data validation not attempted.' >&2
        exit 3
    fi
    if [ "${SH3_MODE:-preflight}" = runtime-diagnostics ]; then
        if [ ! -x "$PORT_ROOT/runtime/sh3" ]; then
            echo 'Native runtime missing; install Docker-built ARM64 diagnostics package.' >&2
            return 3
        fi
        export SDL_GAMECONTROLLERCONFIG="${sdl_controllerconfig:-}"
        if declare -F pm_platform_helper >/dev/null; then
            pm_platform_helper "$PORT_ROOT/runtime/sh3"
        fi
        cd "$RUN_DIR" || return 3
        timeout 30s "$PORT_ROOT/runtime/sh3" --runtime-diagnostics
        return $?
    fi
    bash "${SH3_PACKAGE_DIR:-$PORT_ROOT/preflight}/scripts/device/check-data.sh" "$DATA_DIR" \
        2> "$RUN_DIR/data.stderr.txt"
    local status=$?
    cat "$RUN_DIR/data.stderr.txt" >&2
    if [ "$status" -ne 0 ] && [ "${SH3_PREFLIGHT_HEADLESS:-0}" != 1 ] && \
        declare -F pm_message >/dev/null; then
        pm_message "$(head -n 1 "$RUN_DIR/data.stderr.txt")"
    fi
    return "$status"
}
( main ) > "$RUN_DIR/stdout.txt" 2> "$RUN_DIR/stderr.txt"
status=$?
printf '%s\n' "$status" > "$RUN_DIR/exit-status.txt"
cat "$RUN_DIR/stdout.txt"
cat "$RUN_DIR/stderr.txt" >&2
exit "$status"
