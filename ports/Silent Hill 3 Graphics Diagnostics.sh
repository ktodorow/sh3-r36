#!/bin/bash
# SH3 project graphics diagnostics menu; native GLES, no original assets required at runtime.
export SH3_MODE=gles-diagnostics
export SH3_PORT_ROOT="$(cd "$(dirname "$0")" && pwd)/sh3"
exec bash "$SH3_PORT_ROOT/preflight/ports/Silent Hill 3.sh"
