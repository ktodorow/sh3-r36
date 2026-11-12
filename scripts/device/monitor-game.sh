#!/bin/bash
# Read-only, five-second performance samples; no clock/governor changes.
set -u
OUT=$1
sleeper=
trap 'exit 0' INT TERM HUP
finish() {
    if [ -n "$sleeper" ]; then kill "$sleeper" 2>/dev/null || true; wait "$sleeper" 2>/dev/null || true; fi
}
trap finish EXIT
exec > "$OUT/performance.txt" 2> "$OUT/performance.stderr.txt"
printf 'clock_ticks=%s\n' "$(getconf CLK_TCK)"
while :; do
    printf '\n[sample %s]\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    cat /proc/uptime /proc/loadavg
    head -n 1 /proc/stat
    awk '/MemAvailable:|SwapFree:|Dirty:|Writeback:/ {print}' /proc/meminfo
    for path in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor \
        /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq \
        /sys/devices/system/cpu/cpufreq/policy*/scaling_min_freq \
        /sys/devices/system/cpu/cpufreq/policy*/scaling_max_freq \
        /sys/class/devfreq/*/cur_freq /sys/class/devfreq/*/governor \
        /sys/class/devfreq/*/load /sys/class/thermal/thermal_zone*/temp; do
        if [ -r "$path" ]; then printf '[%s]\n' "$path"; cat "$path"; fi
    done
    for pid in $(pgrep -x sh3); do
        printf '\n[native-process %s]\n' "$pid"
        cat "/proc/$pid/stat" "/proc/$pid/io"
        awk '/VmRSS:|VmHWM:|VmSize:|Threads:|voluntary_ctxt_switches:/ {print}' "/proc/$pid/status"
        ps -L -p "$pid" -o pid,tid,psr,pcpu,stat,comm
    done
    sleep 5 &
    sleeper=$!
    wait "$sleeper" || true
    sleeper=
done
