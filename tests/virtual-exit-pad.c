/* External input fixture: real SDL virtual pad, loaded only in ARM64 Docker tests. */
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdio.h>

int SDL_PollEvent(SDL_Event *event) {
    static int (*poll_event)(SDL_Event *);
    static SDL_Joystick *joystick;
    static Uint64 started;
    static int step;
    static Uint64 next;
    if (!poll_event) poll_event = dlsym(RTLD_NEXT, "SDL_PollEvent");
    if (!joystick && SDL_WasInit(SDL_INIT_GAMECONTROLLER)) {
        int index = SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,
                                            SDL_CONTROLLER_AXIS_MAX, SDL_CONTROLLER_BUTTON_MAX, 0);
        if (index >= 0 && SDL_IsGameController(index)) joystick = SDL_JoystickOpen(index);
        if (!joystick) { fprintf(stderr, "virtual pad failed: %s\n", SDL_GetError()); return poll_event(event); }
        started = SDL_GetTicks64();
        fprintf(stderr, "virtual pad ready\n");
    }
    if (joystick) {
        Uint64 elapsed = SDL_GetTicks64() - started;
        static const int phases[] = {0, 1, 0, 2, 0, 3};
        if (step < 6 && elapsed >= next) {
            int phase = phases[step++];
            SDL_JoystickSetVirtualButton(joystick, SDL_CONTROLLER_BUTTON_START, (phase & 1) != 0);
            SDL_JoystickSetVirtualButton(joystick, SDL_CONTROLLER_BUTTON_BACK, (phase & 2) != 0);
            SDL_JoystickUpdate();
            fprintf(stderr, "virtual pad phase=%d elapsed=%llu\n", phase, (unsigned long long)elapsed);
            next = elapsed + (phase ? 500 : 1000);
        }
    }
    return poll_event(event);
}
