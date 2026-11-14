/* Observe texture-unit work against linked active samplers; forward real GL. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct { GLuint id; unsigned samplers; } programs[512];
static unsigned program_count, requests[8];
static GLuint current;
static unsigned long long draws, selections, inactive;
static PFNGLUSEPROGRAMPROC use_program;
static PFNGLGETUNIFORMLOCATIONPROC uniform_location;
static PFNGLACTIVETEXTUREPROC active_texture;
static void (*draw_arrays)(GLenum, GLint, GLsizei);
static void (*draw_elements)(GLenum, GLsizei, GLenum, const void *);
static PFNGLDRAWELEMENTSBASEVERTEXPROC draw_base;

static unsigned *samplers(GLuint id) {
    for (unsigned i = 0; i < program_count; i++)
        if (programs[i].id == id) return &programs[i].samplers;
    if (program_count == sizeof programs / sizeof *programs) abort();
    programs[program_count].id = id;
    return &programs[program_count++].samplers;
}
static void count_use(GLuint id) { current = id; use_program(id); }
static GLint count_location(GLuint id, const GLchar *name) {
    GLint location = uniform_location(id, name);
    if (name[0] == 's' && name[1] >= '0' && name[1] <= '7' && !name[2] && location >= 0)
        *samplers(id) |= 1u << (name[1] - '0');
    return location;
}
static void count_active(GLenum unit) {
    if (unit >= GL_TEXTURE0 && unit < GL_TEXTURE0 + 8) requests[unit - GL_TEXTURE0]++;
    active_texture(unit);
}
static void observe_draw(void) {
    unsigned mask = *samplers(current);
    draws++;
    for (unsigned i = 0; i < 8; i++) {
        selections += requests[i];
        if (!(mask & (1u << i))) inactive += requests[i];
        requests[i] = 0;
    }
}
static void count_arrays(GLenum mode, GLint first, GLsizei count) {
    observe_draw(); draw_arrays(mode, first, count);
}
static void count_elements(GLenum mode, GLsizei count, GLenum type, const void *indices) {
    observe_draw(); draw_elements(mode, count, type, indices);
}
static void count_base(GLenum mode, GLsizei count, GLenum type, const void *indices, GLint base) {
    observe_draw(); draw_base(mode, count, type, indices, base);
}
void *SDL_GL_GetProcAddress(const char *name) {
    static void *(*next)(const char *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = next(name);
    if (!function) return NULL;
    if (!strcmp(name, "glUseProgram")) { use_program = function; return count_use; }
    if (!strcmp(name, "glGetUniformLocation")) { uniform_location = function; return count_location; }
    if (!strcmp(name, "glActiveTexture")) { active_texture = function; return count_active; }
    if (!strcmp(name, "glDrawArrays")) { draw_arrays = function; return count_arrays; }
    if (!strcmp(name, "glDrawElements")) { draw_elements = function; return count_elements; }
    if (!strcmp(name, "glDrawElementsBaseVertex")) { draw_base = function; return count_base; }
    return function;
}
__attribute__((destructor)) static void report_cost(void) {
    if (draws) fprintf(stderr, "texture_boundary draws=%llu selections=%llu inactive=%llu\n",
                       draws, selections, inactive);
}
