/* Observe real driver submissions without changing them. Linux ARM64 Docker only. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { VIEWPORT, SCALAR, CONSTANT, MATRIX, OTHER, CATEGORIES };
static struct Uniform {
    GLuint program;
    GLint location;
    char name[32];
    unsigned char value[96 * 4 * sizeof(float)];
    size_t bytes;
    GLint active_size;
    int valid;
} uniforms[4096];
static size_t nuniforms;
static GLuint current;
static unsigned long long updates[CATEGORIES], repeats[CATEGORIES], lookup_repeats;
static unsigned long long vertex_constant_updates, excess_vertex_constants;
static void *(*lookup)(const char *);
static PFNGLUSEPROGRAMPROC use_program;
static PFNGLGETUNIFORMLOCATIONPROC get_location;
static PFNGLUNIFORM1FPROC uniform_1f;
static PFNGLUNIFORM2FPROC uniform_2f;
static PFNGLUNIFORM4FVPROC uniform_4fv;
static PFNGLUNIFORMMATRIX4FVPROC uniform_m4;
static PFNGLUNIFORMMATRIX3FVPROC uniform_m3;

static void observe(GLint location, const void *value, size_t bytes, int matrix) {
    if (location < 0) return;
    for (size_t i = 0; i < nuniforms; i++) {
        struct Uniform *u = &uniforms[i];
        if (u->program != current || u->location != location) continue;
        if (bytes > sizeof u->value) abort();
        int category = matrix ? MATRIX :
            !strcmp(u->name, "uHalfPix") || !strcmp(u->name, "uVp") ? VIEWPORT :
            !strcmp(u->name, "c") || !strcmp(u->name, "pc") ? CONSTANT : SCALAR;
        updates[category]++;
        if (u->valid && u->bytes == bytes && !memcmp(u->value, value, bytes)) repeats[category]++;
        memcpy(u->value, value, bytes);
        u->bytes = bytes;
        u->valid = 1;
        return;
    }
    updates[OTHER]++;
}

static void count_program(GLuint program) { current = program; use_program(program); }
static GLint count_location(GLuint program, const GLchar *name) {
    GLint location = get_location(program, name);
    for (size_t i = 0; i < nuniforms; i++)
        if (uniforms[i].program == program && !strcmp(uniforms[i].name, name)) {
            lookup_repeats++;
            return location;
        }
    if (nuniforms == sizeof uniforms / sizeof uniforms[0] || strlen(name) >= sizeof uniforms[0].name) abort();
    struct Uniform *u = &uniforms[nuniforms++];
    u->program = program;
    u->location = location;
    strcpy(u->name, name);
    if (location >= 0 && !strcmp(name, "c")) {
        PFNGLGETPROGRAMIVPROC program_iv = lookup("glGetProgramiv");
        PFNGLGETACTIVEUNIFORMPROC active_uniform = lookup("glGetActiveUniform");
        GLint count;
        program_iv(program, GL_ACTIVE_UNIFORMS, &count);
        for (GLint i = 0; i < count; i++) {
            char active_name[128]; GLint size; GLenum type;
            active_uniform(program, i, sizeof active_name, NULL, &size, &type, active_name);
            if (!strcmp(active_name, "c[0]") || !strcmp(active_name, "c")) {
                if (type != GL_FLOAT_VEC4) abort();
                u->active_size = size;
            }
        }
        if (!u->active_size) abort();
    }
    return location;
}
static void count_1f(GLint loc, GLfloat value) {
    observe(loc, &value, sizeof value, 0); uniform_1f(loc, value);
}
static void count_2f(GLint loc, GLfloat x, GLfloat y) {
    const GLfloat value[] = {x, y};
    observe(loc, value, sizeof value, 0); uniform_2f(loc, x, y);
}
static void count_4fv(GLint loc, GLsizei count, const GLfloat *value) {
    if (loc >= 0) for (size_t i = 0; i < nuniforms; i++) {
        struct Uniform *u = &uniforms[i];
        if (u->program != current || u->location != loc || strcmp(u->name, "c")) continue;
        vertex_constant_updates++;
        if (count > u->active_size) excess_vertex_constants += count - u->active_size;
        break;
    }
    observe(loc, value, count * 4 * sizeof *value, 0); uniform_4fv(loc, count, value);
}
static void count_m4(GLint loc, GLsizei count, GLboolean transpose, const GLfloat *value) {
    if (transpose) abort();
    observe(loc, value, count * 16 * sizeof *value, 1); uniform_m4(loc, count, transpose, value);
}
static void count_m3(GLint loc, GLsizei count, GLboolean transpose, const GLfloat *value) {
    if (transpose) abort();
    observe(loc, value, count * 9 * sizeof *value, 1); uniform_m3(loc, count, transpose, value);
}

void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) lookup = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = lookup(name);
    if (!function) return NULL;
    if (!strcmp(name, "glUseProgram")) { use_program = function; return count_program; }
    if (!strcmp(name, "glGetUniformLocation")) { get_location = function; return count_location; }
    if (!strcmp(name, "glUniform1f")) { uniform_1f = function; return count_1f; }
    if (!strcmp(name, "glUniform2f")) { uniform_2f = function; return count_2f; }
    if (!strcmp(name, "glUniform4fv")) { uniform_4fv = function; return count_4fv; }
    if (!strcmp(name, "glUniformMatrix4fv")) { uniform_m4 = function; return count_m4; }
    if (!strcmp(name, "glUniformMatrix3fv")) { uniform_m3 = function; return count_m3; }
    return function;
}

__attribute__((destructor)) static void report_cost(void) {
    if (!updates[VIEWPORT]) return;
    fprintf(stderr, "uniform_boundary viewport_updates=%llu viewport_repeats=%llu "
            "scalar_updates=%llu scalar_repeats=%llu constant_updates=%llu constant_repeats=%llu "
            "matrix_updates=%llu matrix_repeats=%llu lookup_repeats=%llu unclassified=%llu\n",
            updates[VIEWPORT], repeats[VIEWPORT], updates[SCALAR], repeats[SCALAR],
            updates[CONSTANT], repeats[CONSTANT], updates[MATRIX], repeats[MATRIX],
            lookup_repeats, updates[OTHER]);
    fprintf(stderr, "constant_range updates=%llu excess=%llu\n",
            vertex_constant_updates, excess_vertex_constants);
}
