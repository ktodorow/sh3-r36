#!/usr/bin/env python3
"""Run repeatable owner-checkpoint movement comparison in existing ARM64 environment."""
from datetime import datetime, timezone
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from r36s import ROOT, check_ignores, config

check_ignores()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--seed', type=Path, required=True, help='Collected session containing savedata/data.001 and data.sys')
a = p.parse_args()
seed = a.seed.resolve()
for name in ['data.001', 'data.sys']:
    if not (seed / 'savedata' / name).is_file(): p.error('Missing collected checkpoint files')
image = 'sh3-r36s-build:' + hashlib.sha256((ROOT / 'scripts/build/Dockerfile').read_bytes()).hexdigest()[:16]
out = ROOT / '.port-cache/movement-tests' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out.mkdir(parents=True)
# Test-only external SDL wrapper; no production game timing changes.
(out / 'slow-presentation.c').write_text('''#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdlib.h>
void SDL_GL_SwapWindow(SDL_Window *window) {
    static void (*original)(SDL_Window *);
    if (!original) original = dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
    if (SDL_GetTicks64() >= 48000) SDL_Delay(atoi(getenv("SH3_TEST_SWAP_MS")));
    original(window);
}
''')
game = Path(config().get('SH3_GAME_DIR') or ROOT / 'SILENT HILL 3').expanduser().resolve()
argv = ['docker', 'run', '--rm', '--platform', 'linux/arm64']
for name in ['tests', 'ports', 'scripts', 'dist']:
    argv += ['--mount', f'type=bind,src={ROOT / name},dst=/work/{name},readonly']
argv += ['--mount', f'type=bind,src={game},dst=/owner,readonly',
         '--mount', f'type=bind,src={seed},dst=/seed,readonly',
         '--mount', f'type=bind,src={out},dst=/evidence',
         '-e', 'SH3_MOVEMENT_SEED=/seed', '-e', 'SH3_RUNTIME_BINARY=/work/dist/runtime/sh3',
         '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTHONPATH=/work/tests',
         image, 'bash', '-c',
         'cc -shared -fPIC /evidence/slow-presentation.c -o /evidence/slow-presentation.so -lSDL2 -ldl && '
         'python3 -m unittest test_game_movement.MovementTimingTests -v']
with (out / 'stdout.txt').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
    status = subprocess.run(argv, stdout=stdout, stderr=stderr).returncode
(out / 'exit-status.txt').write_text(str(status) + '\n')
print((out / 'stderr.txt').read_text(), end='')
print('Evidence:', out.relative_to(ROOT))
sys.exit(status)
