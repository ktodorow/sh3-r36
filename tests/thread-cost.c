/* Real GL forwarding: draws/uploads must reach one worker, never loader thread. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

static SDL_threadID loader_thread, draw_thread;
static unsigned long long draws, main_draws, changed_thread, uploads, main_uploads;
static void *(*lookup)(const char *);
static __typeof__(&glDrawArrays) draw_arrays;
static __typeof__(&glDrawElements) draw_elements;
static PFNGLDRAWELEMENTSBASEVERTEXPROC draw_base;
static PFNGLBUFFERDATAPROC buffer_data;
static void observe_draw(void) {
    SDL_threadID current = SDL_ThreadID();
    draws++; main_draws += current == loader_thread;
    if (draw_thread && draw_thread != current) changed_thread++;
    draw_thread = current;
}
static void arrays(GLenum mode, GLint first, GLsizei n) {
    observe_draw(); draw_arrays(mode, first, n);
}
static void elements(GLenum mode, GLsizei n, GLenum type, const void *offset) {
    observe_draw(); draw_elements(mode, n, type, offset);
}
static void base(GLenum mode, GLsizei n, GLenum type, const void *offset, GLint vertex) {
    observe_draw(); draw_base(mode, n, type, offset, vertex);
}
static void upload(GLenum target, GLsizeiptr size, const void *data, GLenum usage) {
    uploads++; main_uploads += SDL_ThreadID() == loader_thread;
    buffer_data(target, size, data, usage);
}
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) { loader_thread = SDL_ThreadID(); lookup = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress"); }
    void *function = lookup(name);
    if (!function) return NULL;
#define WRAP(gl, driver, wrapper) if (!strcmp(name,#gl)) { driver=function; return wrapper; }
    WRAP(glDrawArrays,draw_arrays,arrays)
    WRAP(glDrawElements,draw_elements,elements)
    WRAP(glDrawElementsBaseVertex,draw_base,base)
    WRAP(glBufferData,buffer_data,upload)
#undef WRAP
    return function;
}
__attribute__((destructor)) static void report(void) {
    if (draws) fprintf(stderr, "thread_boundary draws=%llu main_draws=%llu changed_thread=%llu uploads=%llu main_uploads=%llu\n",
                       draws,main_draws,changed_thread,uploads,main_uploads);
}
