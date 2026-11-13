/* External input fixture: real SDL virtual pad, loaded only in ARM64 Docker tests. */
#include <SDL2/SDL.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

int SDL_PollEvent(SDL_Event *event) {
    static int (*poll_event)(SDL_Event *);
    static SDL_Joystick *joystick;
    static Uint64 started;
    static int step;
    static Uint64 next;
    if (!poll_event) poll_event = dlsym(RTLD_NEXT, "SDL_PollEvent");
    if (!joystick && SDL_WasInit(SDL_INIT_GAMECONTROLLER)) {
        int matrix = getenv("SH3_TEST_INPUT_MATRIX") != NULL;
        SDL_VirtualJoystickDesc description = {
            .version = SDL_VIRTUAL_JOYSTICK_DESC_VERSION,
            .type = SDL_JOYSTICK_TYPE_GAMECONTROLLER,
            .naxes = 4, .nbuttons = 17, .vendor_id = 0x484b, .product_id = 0x1100,
            .name = "R36S input fixture"
        };
        int index = matrix ? SDL_JoystickAttachVirtualEx(&description) :
            SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,
                                      SDL_CONTROLLER_AXIS_MAX, SDL_CONTROLLER_BUTTON_MAX, 0);
        if (index >= 0 && matrix) {
            char guid[33], mapping[512];
            SDL_JoystickGetGUIDString(SDL_JoystickGetDeviceGUID(index), guid, sizeof guid);
            snprintf(mapping, sizeof mapping, "%s,R36S input fixture,a:b1,b:b0,x:b2,y:b3,"
                     "leftshoulder:b4,rightshoulder:b5,lefttrigger:b6,righttrigger:b7,"
                     "dpup:b8,dpdown:b9,dpleft:b10,dpright:b11,back:b12,start:b13,"
                     "leftstick:b14,rightstick:b15,leftx:a0,lefty:a1,rightx:a2,righty:a3,", guid);
            if (SDL_GameControllerAddMapping(mapping) < 0)
                fprintf(stderr, "virtual pad mapping failed: %s\n", SDL_GetError());
        }
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
            if (getenv("SH3_TEST_INPUT_MATRIX")) {
                SDL_JoystickSetVirtualButton(joystick, 6, phase == 1);
                SDL_JoystickSetVirtualButton(joystick, 7, phase == 2);
                SDL_JoystickSetVirtualButton(joystick, 13, phase == 3);
                SDL_JoystickSetVirtualButton(joystick, 12, phase == 3);
            } else {
                SDL_JoystickSetVirtualButton(joystick, SDL_CONTROLLER_BUTTON_START, (phase & 1) != 0);
                SDL_JoystickSetVirtualButton(joystick, SDL_CONTROLLER_BUTTON_BACK, (phase & 2) != 0);
            }
            SDL_JoystickUpdate();
            fprintf(stderr, "virtual pad phase=%d elapsed=%llu\n", phase, (unsigned long long)elapsed);
            next = elapsed + (phase ? 500 : 1000);
        }
    }
    return poll_event(event);
}
