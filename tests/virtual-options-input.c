/* External SDL input only; compiled and loaded in ARM64 Docker tests. */
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdio.h>

int SDL_PollEvent(SDL_Event *event) {
    static int (*poll_event)(SDL_Event *);
    static Uint64 started;
    static int step;
    if (!poll_event) poll_event = dlsym(RTLD_NEXT, "SDL_PollEvent");
    if (!started) started = SDL_GetTicks64();
    Uint64 elapsed = SDL_GetTicks64() - started;
    static const struct { Uint64 at; SDL_Keycode key; } keys[] = {
        {6500, SDLK_RETURN}, {9500, SDLK_DOWN}, {10000, SDLK_RETURN},
        {13000, SDLK_DOWN}, {14000, SDLK_RIGHT}, {15000, SDLK_ESCAPE}
    };
    if (step < (int)(sizeof keys / sizeof *keys) && elapsed >= keys[step].at) {
        SDL_Event input = {.type = SDL_KEYDOWN};
        input.key.keysym.sym = keys[step++].key;
        SDL_PushEvent(&input);
        fprintf(stderr, "options fixture step=%d\n", step);
    }
    if (step == 6 && elapsed >= 18000) {
        SDL_Event quit = {.type = SDL_QUIT};
        SDL_PushEvent(&quit);
        step++;
    }
    return poll_event(event);
}
