#!/bin/bash
# Read-only target observations. No helpers sourced, packages installed or display opened.
set -u
# Non-login SSH sessions omit administrative paths; ldconfig -p is read-only.
PATH="$PATH:/usr/sbin:/sbin"
export PATH
PORT_ROOT=$1
RUN_DIR=$2
mkdir -p "$RUN_DIR/helpers" "$RUN_DIR/existing-logs" || exit 3
probe() {
    printf '\n[%s]\n' "$1"
    shift
    if command -v "$1" >/dev/null 2>&1; then
        "$@"
        printf 'probe-exit=%s\n' "$?"
    else
        printf 'missing-tool=%s\n' "$1"
    fi
}
{
    probe kernel uname -srvm
    probe machine uname -m
    probe bitness getconf LONG_BIT
    probe libc getconf GNU_LIBC_VERSION
    probe loader ldd --version
    for path in /etc/os-release /etc/arkos-release /etc/darkos-release \
        /boot/arkos-version /boot/darkos-version "$HOME/.config/.VERSION"; do
        if [ -f "$path" ]; then printf '\n[%s]\n' "$path"; cat "$path"; fi
    done
    for path in /proc/device-tree/compatible /proc/device-tree/model; do
        if [ -r "$path" ]; then printf '\n[%s]\n' "$path"; tr '\000' '\n' < "$path"; fi
    done
    probe memory awk '/MemTotal|MemAvailable|SwapTotal/ {print}' /proc/meminfo
    probe packages dpkg-query -W libc6:arm64 libsdl2-2.0-0:arm64
    probe python python3 --version
    printf '\n[graphics-nodes]\n'
    ls -l /dev/mali0 /dev/dri 2>/dev/null || true
} > "$RUN_DIR/identity.txt" 2> "$RUN_DIR/identity.stderr.txt"
{
    if command -v ldconfig >/dev/null; then
        ldconfig -p | grep -E 'lib(EGL|GLES|GL\.|mali|Mali|SDL2|c\.so)'
        ldconfig -p | awk '/lib(EGL|GLES|GL\.|mali|Mali|SDL2|c\.so)/ {print $NF}' | sort -u |
        while IFS= read -r path; do
            [ -f "$path" ] || continue
            printf '\n[library %s]\n' "$path"
            probe resolved readlink -f "$path"
            probe file file -L "$path"
            probe hash sha256sum "$path"
        done
    else
        echo 'missing-tool=ldconfig'
    fi
} > "$RUN_DIR/libraries.txt" 2> "$RUN_DIR/libraries.stderr.txt"
cat /proc/bus/input/devices > "$RUN_DIR/controllers.txt" 2> "$RUN_DIR/controllers.stderr.txt"
ps -C emulationstation -o pid=,stat=,comm= > "$RUN_DIR/frontend-before.txt" 2>/dev/null || true
awk -v root="$PORT_ROOT" 'index($2,root)==1 {print}' /proc/mounts > "$RUN_DIR/port-mounts-before.txt"
: > "$RUN_DIR/portmaster-files.sha256"
for pm in /opt/system/Tools/PortMaster /opt/tools/PortMaster \
    "${XDG_DATA_HOME:-$HOME/.local/share}/PortMaster" /roms2/ports/PortMaster /roms/ports/PortMaster; do
    [ -f "$pm/control.txt" ] || continue
    # Preserve original paths in checksum record; copy only code/metadata, never settings/secrets.
    find -L "$pm" -maxdepth 1 -type f \( -name control.txt -o -name funcs.txt \
        -o -name 'mod_*.txt' -o -name device_info.txt -o -name mapper.txt \
        -o -name PortMasterDialog.txt -o -name mapper.py -o -name pugwash \) -print |
    sort | while IFS= read -r path; do
        sha256sum "$path" >> "$RUN_DIR/portmaster-files.sha256"
        dest="$RUN_DIR/helpers$path"
        mkdir -p "$(dirname "$dest")"
        cp -p "$path" "$dest"
    done
done
for name in log.txt sh3.log sh3-crash.log; do
    if [ -f "$PORT_ROOT/$name" ]; then
        sha256sum "$PORT_ROOT/$name"
        cp -p "$PORT_ROOT/$name" "$RUN_DIR/existing-logs/$name"
    fi
done > "$RUN_DIR/existing-logs-before.sha256"
# Include completed menu launches without altering originals or recursing into payloads.
for record in "$PORT_ROOT"/runs/*/run-id.txt; do
    [ -f "$record" ] || continue
    launch=$(dirname "$record")
    [ -f "$launch/exit-status.txt" ] || continue
    id=$(basename "$launch")
    case "$id" in ''|*[!A-Za-z0-9_-]*) continue ;; esac
    dest="$RUN_DIR/previous-launches/$id"
    mkdir -p "$dest" || exit 3
    for name in run-id.txt stdout.txt stderr.txt data.stderr.txt exit-status.txt; do
        [ ! -f "$launch/$name" ] || cp -p "$launch/$name" "$dest/" || exit 3
    done
done
echo 'Target observations collected; active SDL backend and GLES operations untested.'
