/* Observe linked vertex outputs at real draws; forward every GL call. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct { GLuint id; int point_size; } programs[512];
static unsigned program_count;
static GLuint current;
static unsigned long long points, other, missing_point_size, unused_point_size;
static void *(*lookup)(const char *);
static PFNGLUSEPROGRAMPROC use_program;
static void (*draw_arrays)(GLenum, GLint, GLsizei);
static void (*draw_elements)(GLenum, GLsizei, GLenum, const void *);
static PFNGLDRAWELEMENTSBASEVERTEXPROC draw_base;

static int writes_point_size(GLuint id) {
    for (unsigned i = 0; i < program_count; i++)
        if (programs[i].id == id) return programs[i].point_size;
    if (program_count == sizeof programs / sizeof *programs) abort();
    PFNGLGETATTACHEDSHADERSPROC attached = lookup("glGetAttachedShaders");
    PFNGLGETSHADERIVPROC shader_iv = lookup("glGetShaderiv");
    PFNGLGETSHADERSOURCEPROC shader_source = lookup("glGetShaderSource");
    GLuint shaders[8]; GLsizei count = 0;
    attached(id, 8, &count, shaders);
    int writes = 0, vertex = 0;
    for (int i = 0; i < count; i++) {
        GLint type, length;
        shader_iv(shaders[i], GL_SHADER_TYPE, &type);
        if (type != GL_VERTEX_SHADER) continue;
        vertex++;
        shader_iv(shaders[i], GL_SHADER_SOURCE_LENGTH, &length);
        if (length <= 0) abort();
        char *source = calloc((size_t)length + 1, 1);
        if (!source) abort();
        shader_source(shaders[i], length, NULL, source);
        writes |= strstr(source, "gl_PointSize") != NULL;
        free(source);
    }
    if (vertex != 1) abort();
    programs[program_count].id = id;
    programs[program_count++].point_size = writes;
    return writes;
}
static void observe_draw(GLenum mode) {
    int writes = writes_point_size(current);
    if (mode == GL_POINTS) { points++; missing_point_size += !writes; }
    else { other++; unused_point_size += writes; }
}
static void count_use(GLuint id) { current = id; use_program(id); }
static void count_arrays(GLenum mode, GLint first, GLsizei count) {
    observe_draw(mode); draw_arrays(mode, first, count);
}
static void count_elements(GLenum mode, GLsizei count, GLenum type, const void *indices) {
    observe_draw(mode); draw_elements(mode, count, type, indices);
}
static void count_base(GLenum mode, GLsizei count, GLenum type, const void *indices, GLint base) {
    observe_draw(mode); draw_base(mode, count, type, indices, base);
}
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) lookup = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = lookup(name);
    if (!function) return NULL;
    if (!strcmp(name, "glUseProgram")) { use_program = function; return count_use; }
    if (!strcmp(name, "glDrawArrays")) { draw_arrays = function; return count_arrays; }
    if (!strcmp(name, "glDrawElements")) { draw_elements = function; return count_elements; }
    if (!strcmp(name, "glDrawElementsBaseVertex")) { draw_base = function; return count_base; }
    return function;
}
__attribute__((destructor)) static void report_cost(void) {
    if (points || other)
        fprintf(stderr, "primitive_boundary points=%llu other=%llu missing=%llu unused=%llu\n",
                points, other, missing_point_size, unused_point_size);
}
