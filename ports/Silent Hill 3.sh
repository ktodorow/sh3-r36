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
    if [ "${SH3_MODE:-preflight}" = runtime-diagnostics ] || [ "${SH3_MODE:-}" = gles-diagnostics ]; then
        if [ ! -x "$PORT_ROOT/runtime/sh3" ]; then
            echo 'Native runtime missing; install Docker-built ARM64 diagnostics package.' >&2
            return 3
        fi
        export SDL_GAMECONTROLLERCONFIG="${sdl_controllerconfig:-}"
        if declare -F pm_platform_helper >/dev/null; then
            pm_platform_helper "$PORT_ROOT/runtime/sh3"
        fi
        cd "$RUN_DIR" || return 3
        timeout 30s "$PORT_ROOT/runtime/sh3" "--$SH3_MODE"
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
    if [ "$status" -eq 0 ] && [ "${SH3_MODE:-}" = game ]; then
        if [ ! -x "$PORT_ROOT/runtime/sh3" ]; then
            echo 'Native runtime missing; install Docker-built ARM64 game package.' >&2
            return 3
        fi
        # Ordinary play keeps state across launches; diagnostic replays stay isolated.
        local session="$PORT_ROOT/state"
        if [ "${SH3_SESSION_ISOLATED:-0}" = 1 ] || [ -n "${SH3_SEED_SESSION:-}" ]; then
            session="$RUN_DIR/session"
        fi
        state_failure() {
            local message="Cannot use save/settings folder: $1. Existing files preserved."
            echo "$message" >&2
            if [ "${SH3_PREFLIGHT_HEADLESS:-0}" != 1 ] && declare -F pm_message >/dev/null; then
                pm_message "$message"
            fi
            return 3
        }
        if [ -n "${SH3_IMPORT_SESSION:-}" ]; then
            if [ "$session" != "$PORT_ROOT/state" ] || [ -e "$session" ] || [ -L "$session" ]; then
                state_failure 'import requires an absent player-state folder and ordinary game mode'
                return 3
            fi
            if [ ! -d "$SH3_IMPORT_SESSION/savedata" ]; then
                state_failure 'selected import has no savedata folder'
                return 3
            fi
            local stage="$RUN_DIR/state-init" path
            mkdir -p "$stage/savedata" || { state_failure 'cannot prepare import'; return 3; }
            for path in "$SH3_IMPORT_SESSION"/savedata/data.[0-9][0-9][0-9] \
                "$SH3_IMPORT_SESSION"/savedata/data.sys "$SH3_IMPORT_SESSION"/savedata/disp.ini \
                "$SH3_IMPORT_SESSION"/savedata/key.ini "$SH3_IMPORT_SESSION"/sh3.ini \
                "$SH3_IMPORT_SESSION"/sh3-progs.bin "$SH3_IMPORT_SESSION"/sh3-gl-cache.bin; do
                [ -f "$path" ] || continue
                local target="$stage/$(basename "$path")"
                case "$path" in "$SH3_IMPORT_SESSION"/savedata/*) target="$stage/savedata/$(basename "$path")" ;; esac
                if ! cp -p "$path" "$target" || ! chmod u+rw "$target"; then
                    state_failure 'cannot copy selected import; check free space and write access'
                    return 3
                fi
            done
            mv "$stage" "$session" || { state_failure 'cannot install imported state'; return 3; }
            echo 'Imported prior saves and preferences; source preserved.'
        fi
        if [ -L "$session" ] || ! mkdir -p "$session"; then
            state_failure 'check conflicting files, free space and write access'
            return 3
        fi
        printf 'state: %s\n' "$session"
        if [ -n "${SH3_SEED_SESSION:-}" ]; then
            for name in data.001 data.sys; do
                [ -f "$SH3_SEED_SESSION/savedata/$name" ] || {
                    echo 'Checkpoint missing data.001 or data.sys.' >&2; return 3;
                }
            done
            mkdir "$session/savedata" || return 3
            for name in data.001 data.sys disp.ini key.ini; do
                if [ -f "$SH3_SEED_SESSION/savedata/$name" ]; then
                    cp -p "$SH3_SEED_SESSION/savedata/$name" "$session/savedata/$name" || return 3
                fi
            done
            for name in sh3-progs.bin sh3-gl-cache.bin; do
                if [ -f "$SH3_SEED_SESSION/$name" ]; then
                    cp -p "$SH3_SEED_SESSION/$name" "$session/$name" || return 3
                fi
            done
        fi
        if [ -n "${SH3_SHOT:-}" ]; then mkdir -p "$SH3_SHOT" || return 3; fi
        if [ -n "${SH3_INTERNAL_RESOLUTION:-}" ]; then
            case "$SH3_INTERNAL_RESOLUTION" in
                640x480|320x240) ;;
                *) echo 'Unsupported internal resolution.' >&2; return 3 ;;
            esac
            mkdir -p "$session/savedata" || return 3
            local display="$session/savedata/disp.ini"
            if [ ! -s "$display" ]; then
                printf '%s\n' 'format=D3DFMT_A8R8G8B8' 'gamma_b=1' 'gamma_g=1' \
                    'gamma_r=1' 'lensflare_ztest=1' 'mode=fullscreen' \
                    'shadow=1' 'size=640x480' > "$display" || return 3
            fi
            : > "$display.new" || return 3
            if [ -f "$display" ]; then
                sed '/^resolution=/d' "$display" > "$display.new" || return 3
            fi
            printf 'resolution=%s\n' "$SH3_INTERNAL_RESOLUTION" >> "$display.new" || return 3
            if [ "${SH3_FPS_LIMIT:-}" = 30 ] && [ "$SH3_INTERNAL_RESOLUTION" = 320x240 ]; then
                # Keep explicit performance selection identical to measured scene settings.
                sed -i '/^shadow=/d; /^lensflare_ztest=/d' "$display.new" || return 3
                printf '%s\n' 'shadow=1' 'lensflare_ztest=1' >> "$display.new" || return 3
            fi
            mv "$display.new" "$display" || return 3
        fi
        if [ ! -e "$session/sh3.ini" ]; then
            printf 'resolution=640x480\ncores=3\n' > "$session/sh3.ini" || return 3
        fi
        export SH3_DATA_DIR="$DATA_DIR"
        export SH3_OUTPUT_RESOLUTION=640x480
        export SDL_GAMECONTROLLERCONFIG="${sdl_controllerconfig:-}"
        if declare -F pm_platform_helper >/dev/null; then
            pm_platform_helper "$PORT_ROOT/runtime/sh3"
        fi
        cd "$session" || return 3
        "$PORT_ROOT/runtime/sh3" "$session"
        status=$?
        if [ "$session" != "$RUN_DIR/session" ]; then
            mkdir "$RUN_DIR/session" || return 3
            for name in savedata sh3.ini sh3-progs.bin sh3-gl-cache.bin sh3-crash.log; do
                if [ -e "$session/$name" ]; then
                    cp -Rp "$session/$name" "$RUN_DIR/session/$name" || return 3
                fi
            done
        fi
        return "$status"
    fi
    return "$status"
}
( main ) > "$RUN_DIR/stdout.txt" 2> "$RUN_DIR/stderr.txt"
status=$?
printf '%s\n' "$status" > "$RUN_DIR/exit-status.txt"
cat "$RUN_DIR/stdout.txt"
cat "$RUN_DIR/stderr.txt" >&2
exit "$status"
