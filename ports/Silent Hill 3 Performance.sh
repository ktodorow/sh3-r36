#!/bin/bash
# SH3 project performance menu; 320x240 rendering, 640x480 output, 30 FPS cap.
export SH3_FPS_LIMIT=30 SH3_INTERNAL_RESOLUTION=320x240
exec bash "$(dirname "$0")/Silent Hill 3 Game.sh" "$@"
