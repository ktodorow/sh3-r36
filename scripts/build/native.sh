#!/bin/bash
# Executed only by saved Docker host workflow, never on host or handheld.
set -euo pipefail
[ "$(uname -m)" = aarch64 ] || { echo 'Requires native Linux ARM64 container' >&2; exit 3; }
case "${SH3_OPTIMIZATION:-O2}" in
    O2|O3) ;;
    *) echo 'Unsupported optimization variant' >&2; exit 3 ;;
esac
case "${SH3_LTO:-0}" in
    0) lto_flag='' ;;
    1) lto_flag='-flto=2' ;;
    *) echo 'Unsupported LTO variant' >&2; exit 3 ;;
esac
mkdir -p build/arm64 dist/runtime
dpkg-query -W > build/arm64/packages.txt
cc --version > build/arm64/compiler.txt
getconf GNU_LIBC_VERSION > build/arm64/libc.txt
"$SH3_PYTHON" -m pip freeze > build/arm64/python.txt
# Reuse only byte-verified output from identical input, generator and image.
if [ -f build/generation-key.txt ] && [ "$(cat build/generation-key.txt)" = "$SH3_GENERATION_KEY" ] && \
    [ -s build/generated.sha256 ] && sha256sum -c build/generated.sha256 >/dev/null 2>&1; then
    echo 'Reusing verified generated code.'
else
    sh tools/regen.sh > build/arm64/generation.stdout.txt 2> build/arm64/generation.stderr.txt
    find src/recomp/gen -type f -print0 | sort -z | xargs -0 sha256sum > build/generated.sha256
    printf '%s\n' "$SH3_GENERATION_KEY" > build/generation-key.txt
fi
"$SH3_PYTHON" scripts/build/shader-samples.py "$SH3_EXE" build/arm64/generated/shader_samples.h
cmake -S . -B build/arm64 -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DNINTENDO_SWITCH=OFF -DSH3_GLES_SAMPLES=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DCMAKE_C_FLAGS_RELWITHDEBINFO="-${SH3_OPTIMIZATION:-O2} -g -DNDEBUG" \
    -DCMAKE_C_FLAGS="-mcpu=cortex-a35 -ffile-prefix-map=/work=.${lto_flag:+ $lto_flag}" \
    -DCMAKE_EXE_LINKER_FLAGS="-fwrapv -fno-strict-aliasing${lto_flag:+ $lto_flag}"
cmake --build build/arm64 --parallel "${SH3_BUILD_JOBS:-2}"
objcopy --only-keep-debug build/arm64/sh3 dist/runtime/sh3.debug
strip --strip-unneeded -o dist/runtime/sh3 build/arm64/sh3
objcopy --add-gnu-debuglink=dist/runtime/sh3.debug dist/runtime/sh3
file dist/runtime/sh3 > dist/runtime/elf.txt
readelf -h -l -d -V dist/runtime/sh3 > dist/runtime/readelf.txt
(cd dist/runtime && sha256sum sh3 > artifacts.sha256)
