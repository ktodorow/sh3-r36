/* Forward real driver calls; distinguish translated game shaders from presenter. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static PFNGLSHADERSOURCEPROC source;
static PFNGLCOMPILESHADERPROC compile;
static PFNGLPROGRAMBINARYPROC load;
static unsigned char translated[65536];
static unsigned compiled, loaded;
static const GLubyte *(*get_string)(GLenum);
static const GLubyte *observe_string(GLenum name) {
    const char *driver = getenv("SH3_TEST_CACHE_DRIVER");
    return name == GL_RENDERER && driver ? (const GLubyte *)driver : get_string(name);
}

static void observe_source(GLuint shader, GLsizei count, const GLchar *const *text,
                           const GLint *lengths) {
    if (shader < sizeof translated) {
        translated[shader] = 0;
        for (int i = 0; i < count; i++)
            if (strstr(text[i], "vs_main(p,") || strstr(text[i], "ps_main(vD0, vD1)"))
                translated[shader] = 1;
    }
    source(shader, count, text, lengths);
}
static void observe_compile(GLuint shader) {
    if (shader < sizeof translated && translated[shader]) compiled++;
    compile(shader);
}
static void observe_load(GLuint program, GLenum format, const void *data, GLsizei bytes) {
    loaded++;
    load(program, format, data, bytes);
}
void *SDL_GL_GetProcAddress(const char *name) {
    static void *(*next)(const char *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = next(name);
    if (!function) return NULL;
    if (!strcmp(name, "glShaderSource")) { source = function; return observe_source; }
    if (!strcmp(name, "glCompileShader")) { compile = function; return observe_compile; }
    if (!strcmp(name, "glProgramBinary")) { load = function; return observe_load; }
    if (!strcmp(name, "glGetString")) { get_string = function; return observe_string; }
    return function;
}
__attribute__((destructor)) static void report(void) {
    if (compiled || loaded)
        fprintf(stderr, "shader_cache_boundary compiled=%u loaded=%u\n", compiled, loaded);
}
