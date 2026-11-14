/* Count calls at real SDL/GL boundary; forward unchanged to Mesa. Docker only. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

static unsigned long long parameters, draws, attributes;
static PFNGLSAMPLERPARAMETERIPROC sampler_i;
static PFNGLSAMPLERPARAMETERFVPROC sampler_fv;
static void (*draw_arrays)(GLenum, GLint, GLsizei);
static void (*draw_elements)(GLenum, GLsizei, GLenum, const void *);
static PFNGLDRAWELEMENTSBASEVERTEXPROC draw_base;
static PFNGLENABLEVERTEXATTRIBARRAYPROC enable_attribute;
static PFNGLDISABLEVERTEXATTRIBARRAYPROC disable_attribute;

static void count_i(GLuint sampler, GLenum name, GLint value) {
    parameters++; sampler_i(sampler, name, value);
}
static void count_fv(GLuint sampler, GLenum name, const GLfloat *value) {
    parameters++; sampler_fv(sampler, name, value);
}
static void count_arrays(GLenum mode, GLint first, GLsizei count) {
    draws++; draw_arrays(mode, first, count);
}
static void count_elements(GLenum mode, GLsizei count, GLenum type, const void *indices) {
    draws++; draw_elements(mode, count, type, indices);
}
static void count_base(GLenum mode, GLsizei count, GLenum type, const void *indices, GLint base) {
    draws++; draw_base(mode, count, type, indices, base);
}
static void count_enable(GLuint index) { attributes++; enable_attribute(index); }
static void count_disable(GLuint index) { attributes++; disable_attribute(index); }

void *SDL_GL_GetProcAddress(const char *name) {
    static void *(*next)(const char *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = next(name);
    if (!function) return NULL;
    if (!strcmp(name, "glSamplerParameteri")) { sampler_i = function; return count_i; }
    if (!strcmp(name, "glSamplerParameterfv")) { sampler_fv = function; return count_fv; }
    if (!strcmp(name, "glDrawArrays")) { draw_arrays = function; return count_arrays; }
    if (!strcmp(name, "glDrawElements")) { draw_elements = function; return count_elements; }
    if (!strcmp(name, "glDrawElementsBaseVertex")) { draw_base = function; return count_base; }
    if (!strcmp(name, "glEnableVertexAttribArray")) { enable_attribute = function; return count_enable; }
    if (!strcmp(name, "glDisableVertexAttribArray")) { disable_attribute = function; return count_disable; }
    return function;
}

__attribute__((destructor)) static void report_cost(void) {
    if (draws) fprintf(stderr, "sampler_boundary draws=%llu parameters=%llu attributes=%llu\n",
                       draws, parameters, attributes);
}
