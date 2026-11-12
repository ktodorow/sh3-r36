#!/bin/bash
# Read-only supported-executable check; usable underneath public launcher.
DATA_DIR=$1
check_executable() {
    if [ ! -f "$DATA_DIR/sh3.exe" ]; then
        echo 'Missing sh3.exe. Supply supported PC executable with data/ in gamedata/.' >&2
        return 2
    fi
    size=$(wc -c < "$DATA_DIR/sh3.exe")
    if [ "$size" -ne 3338240 ]; then
        echo "Unsupported sh3.exe: expected 3338240 bytes; found $size. Original preserved." >&2
        return 2
    fi
    if command -v sha1sum >/dev/null; then
        sha=$(sha1sum "$DATA_DIR/sh3.exe")
    elif command -v shasum >/dev/null; then
        sha=$(shasum -a 1 "$DATA_DIR/sh3.exe")
    else
        echo 'SHA-1 tool missing; executable cannot be verified.' >&2
        return 3
    fi
    sha=${sha%% *}
    case "$sha" in
        aa2aca6dba19bf510c9c2e92eefdc15e98266581) profile=upstream-aa2aca6d ;;
        d851669ef609b3164e3581aa8dcfbfaec866cb79) profile=owner-cd-d851669e ;;
        *)
            echo "Unsupported sh3.exe: expected SHA-1 aa2aca6dba19bf510c9c2e92eefdc15e98266581 (upstream) or d851669ef609b3164e3581aa8dcfbfaec866cb79 (owner CD); found $sha. Original preserved." >&2
            return 2
            ;;
    esac
    printf 'Input profile: %s; %s bytes; SHA-1 %s\n' "$profile" "$size" "$sha"
    echo 'Native runtime must be generated from this input profile; gameplay compatibility untested.'
}
check_executable
status=$?
manifest="$(dirname "$0")/../required-data.txt"
if [ ! -r "$manifest" ]; then
    echo "Required-data manifest unavailable; preflight cannot verify completeness." >&2
    exit 3
fi
while IFS= read -r path; do
    case "$path" in ""|\#*) continue ;; esac
    if [ ! -f "$DATA_DIR/$path" ] || [ ! -s "$DATA_DIR/$path" ]; then
        echo "Missing or empty required data: $path" >&2
        [ "$status" -ne 0 ] || status=2
    else
        printf "data-file\t%s\t%s\n" "$path" "$(wc -c < "$DATA_DIR/$path" | tr -d ' ')"
        if [ "${SH3_DATA_HASHES:-0}" = 1 ]; then
            if command -v sha256sum >/dev/null; then
                digest=$(sha256sum "$DATA_DIR/$path")
            elif command -v shasum >/dev/null; then
                digest=$(shasum -a 256 "$DATA_DIR/$path")
            else
                echo 'SHA-256 tool missing; data identity cannot be recorded.' >&2
                exit 3
            fi
            hash_status=$?
            [ "$hash_status" -eq 0 ] || exit 3
            printf 'data-sha256\t%s\t%s\n' "$path" "${digest%% *}"
        fi
    fi
done < "$manifest"
[ "$status" -ne 0 ] || echo "Supported executable and required-data paths verified; gameplay remains untested."
exit "$status"
