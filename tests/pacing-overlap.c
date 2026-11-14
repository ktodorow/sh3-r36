/* Forward real SDL calls; observe input work during post-swap throttle sleeps. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdatomic.h>
#include <stdio.h>

static _Atomic(SDL_threadID) render_thread;
static atomic_uint probing, polls, total_polls;
static unsigned sleeps, productive_sleeps;

const Uint8 *SDL_GetKeyboardState(int *count) {
    static _Thread_local const Uint8 *(*keyboard)(int *);
    if (!keyboard) keyboard = dlsym(RTLD_NEXT, "SDL_GetKeyboardState");
    atomic_fetch_add(&total_polls, 1);
    if (atomic_load(&probing)) atomic_fetch_add(&polls, 1);
    return keyboard(count);
}

void SDL_GL_SwapWindow(SDL_Window *window) {
    static _Thread_local void (*swap)(SDL_Window *);
    if (!swap) swap = dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
    atomic_store(&render_thread, SDL_ThreadID());
    swap(window);
}

void SDL_Delay(Uint32 ms) {
    static _Thread_local void (*delay)(Uint32);
    if (!delay) delay = dlsym(RTLD_NEXT, "SDL_Delay");
    Uint64 now = SDL_GetTicks64();
    if (SDL_ThreadID() == atomic_load(&render_thread) && now >= 20000 && now < 26000 && ms) {
        unsigned before = atomic_load(&polls);
        atomic_store(&probing, 1);
        /* A long external-boundary wait makes lost overlap deterministic;
         * this artificial stall is never a device performance measurement. */
        delay(ms + 40);
        atomic_store(&probing, 0);
        productive_sleeps += atomic_load(&polls) > before;
        sleeps++;
    } else delay(ms);
}

__attribute__((destructor)) static void report(void) {
    fprintf(stderr, "pacing_overlap sleeps=%u productive=%u input_polls=%u total_polls=%u\n",
            sleeps, productive_sleeps, atomic_load(&polls), atomic_load(&total_polls));
}
