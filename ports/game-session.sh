#!/bin/bash
# Detached native session; stop frontend only after recovery is armed.
set -u
PORT_ROOT=$SH3_PORT_ROOT
RUN_ID=$SH3_RUN_ID
SERVICE_DIR="$PORT_ROOT/runs/${RUN_ID}-service"
privilege=()
monitor=
if [ "$(id -u)" -ne 0 ]; then privilege=(sudo -n); fi
cleanup() {
    local status=$?
    trap - EXIT
    if [ -n "$monitor" ]; then kill "$monitor" 2>/dev/null || true; wait "$monitor" 2>/dev/null || true; fi
    if ! bash "$PORT_ROOT/preflight/ports/restore-frontend.sh" "$PORT_ROOT" "$RUN_ID"; then
        if [ "$status" -eq 0 ]; then status=3; fi
    fi
    printf '%s\n' "$status" > "$SERVICE_DIR/exit-status.txt"
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
if [ ! -r "/proc/$$/cgroup" ] || grep -q 'emulationstation.service' "/proc/$$/cgroup"; then
    echo 'Game still belongs to frontend process group; refusing to stop frontend.' >&2
    exit 3
fi
cat "/proc/$$/cgroup" > "$SERVICE_DIR/cgroup.txt"
free -k > "$SERVICE_DIR/memory-before.txt"
if systemctl is-active --quiet emulationstation.service; then
    touch "$SERVICE_DIR/frontend-stopped" || exit 3
    "${privilege[@]}" systemctl stop emulationstation.service || exit 3
    if systemctl is-active --quiet emulationstation.service || pgrep -x emulationstatio >/dev/null; then
        echo 'Frontend remains running; game not started.' >&2
        exit 3
    fi
    echo 'Frontend stopped for native game.'
fi
free -k > "$SERVICE_DIR/memory-game.txt"
systemctl show emulationstation.service -p ActiveState -p MainPID > "$SERVICE_DIR/frontend-game.txt"
if [ "${SH3_MONITOR:-0}" = 1 ]; then
    bash "$PORT_ROOT/preflight/scripts/device/monitor-game.sh" "$SERVICE_DIR" &
    monitor=$!
fi
bash "$PORT_ROOT/preflight/ports/Silent Hill 3.sh"
exit $?
