/* Observe SDL boundary calls without changing input or time. ARM64 Docker only. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdio.h>

static unsigned long long polls, names;

const Uint8 *SDL_GetKeyboardState(int *count) {
    static const Uint8 *(*next)(int *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GetKeyboardState");
    polls++;
    return next(count);
}

SDL_Scancode SDL_GetScancodeFromName(const char *name) {
    static SDL_Scancode (*next)(const char *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GetScancodeFromName");
    names++;
    return next(name);
}

__attribute__((destructor)) static void report_cost(void) {
    if (polls) fprintf(stderr, "input_boundary polls=%llu names=%llu\n", polls, names);
}
