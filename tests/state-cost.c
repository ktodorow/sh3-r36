/* Forward real GL state calls; observe repeated work at the driver boundary. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

static unsigned long long updates, repeats;
static unsigned char valid[6], enabled[6];
static void (*enable)(GLenum), (*disable)(GLenum);
static void (*viewport)(GLint, GLint, GLsizei, GLsizei);
static void (*depth_range)(GLdouble, GLdouble);
static void (*depth_mask)(GLboolean);
static void (*color_mask)(GLboolean, GLboolean, GLboolean, GLboolean);
static void (*depth_func)(GLenum);
static unsigned long long raster_updates, raster_repeats;
static unsigned char raster_valid[5], raster_value[5][4 * sizeof(GLdouble)];
static PFNGLBINDSAMPLERPROC bind_sampler;
static GLuint sampler[8];
static unsigned char sampler_valid[8];
static unsigned long long sampler_updates, sampler_repeats;
static PFNGLUSEPROGRAMPROC use_program;
static GLuint program;
static unsigned char program_valid;
static unsigned long long program_updates, program_repeats;

static void count_program(GLuint name) {
    program_updates++;
    if (program_valid && program == name) program_repeats++;
    program = name; program_valid = 1;
    use_program(name);
}

static void count_sampler(GLuint unit, GLuint name) {
    if (unit < 8) {
        sampler_updates++;
        if (sampler_valid[unit] && sampler[unit] == name) sampler_repeats++;
        sampler[unit] = name; sampler_valid[unit] = 1;
    }
    bind_sampler(unit, name);
}

static void observe_raster(int i, const void *value, size_t bytes) {
    raster_updates++;
    if (raster_valid[i] && !memcmp(raster_value[i], value, bytes)) raster_repeats++;
    memcpy(raster_value[i], value, bytes);
    raster_valid[i] = 1;
}
static void count_viewport(GLint x, GLint y, GLsizei w, GLsizei h) {
    const GLint v[] = {x,y,w,h}; observe_raster(0, v, sizeof v); viewport(x,y,w,h);
}
static void count_depth_range(GLdouble n, GLdouble f) {
    const GLdouble v[] = {n,f}; observe_raster(1, v, sizeof v); depth_range(n,f);
}
static void count_depth_mask(GLboolean v) {
    observe_raster(2, &v, sizeof v); depth_mask(v);
}
static void count_color_mask(GLboolean r, GLboolean g, GLboolean b, GLboolean a) {
    const GLboolean v[] = {r,g,b,a}; observe_raster(3, v, sizeof v); color_mask(r,g,b,a);
}
static void count_depth_func(GLenum v) {
    observe_raster(4, &v, sizeof v); depth_func(v);
}

static int cap_index(GLenum cap) {
    switch (cap) {
    case GL_SCISSOR_TEST: return 0;
    case GL_DEPTH_TEST: return 1;
    case GL_BLEND: return 2;
    case GL_CULL_FACE: return 3;
    case GL_STENCIL_TEST: return 4;
    case GL_POLYGON_OFFSET_FILL: return 5;
    default: return -1;
    }
}
static void observe(GLenum cap, int value) {
    int i = cap_index(cap);
    if (i < 0) return;
    updates++;
    if (valid[i] && enabled[i] == value) repeats++;
    valid[i] = 1;
    enabled[i] = value;
}
static void count_enable(GLenum cap) { observe(cap, 1); enable(cap); }
static void count_disable(GLenum cap) { observe(cap, 0); disable(cap); }

void *SDL_GL_GetProcAddress(const char *name) {
    static void *(*next)(const char *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = next(name);
    if (!function) return NULL;
    if (!strcmp(name, "glEnable")) { enable = function; return count_enable; }
    if (!strcmp(name, "glDisable")) { disable = function; return count_disable; }
    if (!strcmp(name, "glViewport")) { viewport = function; return count_viewport; }
    if (!strcmp(name, "glDepthRange")) { depth_range = function; return count_depth_range; }
    if (!strcmp(name, "glDepthMask")) { depth_mask = function; return count_depth_mask; }
    if (!strcmp(name, "glColorMask")) { color_mask = function; return count_color_mask; }
    if (!strcmp(name, "glDepthFunc")) { depth_func = function; return count_depth_func; }
    if (!strcmp(name, "glBindSampler")) { bind_sampler = function; return count_sampler; }
    if (!strcmp(name, "glUseProgram")) { use_program = function; return count_program; }
    return function;
}
__attribute__((destructor)) static void report_cost(void) {
    if (updates) fprintf(stderr, "state_boundary updates=%llu repeats=%llu\n", updates, repeats);
    if (raster_updates) fprintf(stderr, "raster_boundary updates=%llu repeats=%llu\n", raster_updates, raster_repeats);
    if (sampler_updates) fprintf(stderr, "sampler_bind_boundary updates=%llu repeats=%llu\n", sampler_updates, sampler_repeats);
    if (program_updates) fprintf(stderr, "program_boundary updates=%llu repeats=%llu\n", program_updates, program_repeats);
}
