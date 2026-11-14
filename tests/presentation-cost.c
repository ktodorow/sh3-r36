/* Observe presentation copies at real GL/SDL boundaries; forward every call. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *(*lookup)(const char *);
static PFNGLBINDFRAMEBUFFERPROC bind_framebuffer;
static PFNGLBLITFRAMEBUFFERPROC blit_framebuffer;
static GLuint draw_framebuffer;
static unsigned screen_blits, offscreen_blits;

static void observe_bind(GLenum target, GLuint framebuffer) {
    if (target == GL_FRAMEBUFFER || target == GL_DRAW_FRAMEBUFFER)
        draw_framebuffer = framebuffer;
    bind_framebuffer(target, framebuffer);
}
static void observe_blit(GLint sx0, GLint sy0, GLint sx1, GLint sy1,
                         GLint dx0, GLint dy0, GLint dx1, GLint dy1,
                         GLbitfield mask, GLenum filter) {
    if (draw_framebuffer) offscreen_blits++; else screen_blits++;
    blit_framebuffer(sx0, sy0, sx1, sy1, dx0, dy0, dx1, dy1, mask, filter);
}
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) lookup = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = lookup(name);
    if (!function) return NULL;
    if (!strcmp(name, "glBindFramebuffer")) {
        bind_framebuffer = function; return observe_bind;
    }
    if (!strcmp(name, "glBlitFramebuffer")) {
        blit_framebuffer = function; return observe_blit;
    }
    return function;
}
void SDL_GL_SwapWindow(SDL_Window *window) {
    static void (*swap)(SDL_Window *);
    if (!swap) swap = dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
    const char *delay = getenv("SH3_TEST_SWAP_MS");
    if (delay) SDL_Delay((Uint32)strtoul(delay,NULL,10));
    swap(window);
    fprintf(stderr, "presentation_boundary screen=%u offscreen=%u\n", screen_blits, offscreen_blits);
    screen_blits = offscreen_blits = 0;
}
