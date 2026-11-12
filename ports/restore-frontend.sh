#!/bin/bash
# Idempotent recovery, also called as privileged service ExecStopPost after crashes.
set -u
unset LD_LIBRARY_PATH LD_PRELOAD
PORT_ROOT=$1
RUN_ID=$2
case "$RUN_ID" in ''|*[!A-Za-z0-9_-]*) echo 'Invalid recovery run ID' >&2; exit 3 ;; esac
SERVICE_DIR="$PORT_ROOT/runs/${RUN_ID}-service"
[ -f "$SERVICE_DIR/frontend-stopped" ] || exit 0
privilege=()
if [ "$(id -u)" -ne 0 ]; then privilege=(sudo -n); fi
"${privilege[@]}" systemctl reset-failed emulationstation.service || true
"${privilege[@]}" systemctl start emulationstation.service || exit 3
for attempt in {1..30}; do
    if systemctl is-active --quiet emulationstation.service && pgrep -x emulationstatio >/dev/null; then
        echo 'Frontend restored.'
        free -k > "$SERVICE_DIR/memory-restored.txt"
        systemctl show emulationstation.service -p ActiveState -p MainPID > "$SERVICE_DIR/frontend-restored.txt"
        rm "$SERVICE_DIR/frontend-stopped"
        exit $?
    fi
    sleep 1
done
echo 'Frontend restore failed; recovery marker retained.' >&2
exit 3
