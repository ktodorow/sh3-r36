#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdio.h>

/* External input latency models a frame near target budget without changing
 * guest clocks, game state, GL output or simulation arithmetic. */
static unsigned delayed;
static double total_delay_ms, max_delay_ms;
const Uint8 *SDL_GetKeyboardState(int *count) {
    static const Uint8 *(*original)(int *);
    if (!original) original = dlsym(RTLD_NEXT, "SDL_GetKeyboardState");
    Uint64 now = SDL_GetTicks64();
    if (now >= 48000 && now < 61000) {
        Uint64 frequency = SDL_GetPerformanceFrequency();
        Uint64 start = SDL_GetPerformanceCounter();
        Uint64 deadline = start + frequency * 32 / 1000;
        /* VM SDL sleeps overshoot by4–10ms. Sleep first, then consume remaining
         * test-only latency against real monotonic time; game clocks untouched. */
        SDL_Delay(24);
        Uint64 end;
        do { end = SDL_GetPerformanceCounter(); } while (end < deadline);
        double duration = 1000.0 * (end - start) / frequency;
        total_delay_ms += duration;
        if (duration > max_delay_ms) max_delay_ms = duration;
        delayed++;
    }
    return original(count);
}
__attribute__((destructor)) static void report(void) {
    if (delayed) fprintf(stderr, "frame_budget delayed_input_polls=%u delay_ms=32 observed_mean_ms=%.6f observed_max_ms=%.6f\n",
                         delayed, total_delay_ms / delayed, max_delay_ms);
}
