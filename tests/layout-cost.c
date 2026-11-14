/* Observe vertex state at real GL boundary, forwarding every request. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static PFNGLBINDBUFFERPROC bind_buffer;
static PFNGLDELETEBUFFERSPROC delete_buffers;
static PFNGLBINDVERTEXARRAYPROC bind_array;
static PFNGLVERTEXATTRIBPOINTERPROC pointer;
static GLuint buffer;
static unsigned char buffer_valid;
static unsigned long long buffer_updates, buffer_repeats, layout_updates, layout_repeats;
static struct {
    GLuint buffer;
    GLint size;
    GLenum type;
    GLboolean normalized, valid;
    GLsizei stride;
    const void *offset;
} attributes[16];

static void count_buffer(GLenum target, GLuint name) {
    if (target == GL_ARRAY_BUFFER) {
        buffer_updates++;
        if (buffer_valid && buffer == name) buffer_repeats++;
        buffer = name; buffer_valid = 1;
    }
    bind_buffer(target, name);
}
static void count_delete(GLsizei n, const GLuint *names) {
    memset(attributes, 0, sizeof attributes);
    buffer_valid = 0;
    delete_buffers(n, names);
}
static void count_array(GLuint name) {
    memset(attributes, 0, sizeof attributes);
    bind_array(name);
}
static void count_pointer(GLuint i, GLint size, GLenum type, GLboolean normalized,
                          GLsizei stride, const void *offset) {
    layout_updates++;
    if (i < 16) {
        if (attributes[i].valid && attributes[i].buffer == buffer &&
            attributes[i].size == size && attributes[i].type == type &&
            attributes[i].normalized == normalized && attributes[i].stride == stride &&
            attributes[i].offset == offset) layout_repeats++;
        attributes[i].buffer = buffer; attributes[i].size = size; attributes[i].type = type;
        attributes[i].normalized = normalized; attributes[i].stride = stride;
        attributes[i].offset = offset; attributes[i].valid = buffer_valid;
    }
    pointer(i, size, type, normalized, stride, offset);
}
void *SDL_GL_GetProcAddress(const char *name) {
    static void *(*next)(const char *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GL_GetProcAddress");
    void *function = next(name);
    if (!function) return NULL;
    if (!strcmp(name, "glBindBuffer")) { bind_buffer = function; return count_buffer; }
    if (!strcmp(name, "glDeleteBuffers")) { delete_buffers = function; return count_delete; }
    if (!strcmp(name, "glBindVertexArray")) { bind_array = function; return count_array; }
    if (!strcmp(name, "glVertexAttribPointer")) { pointer = function; return count_pointer; }
    return function;
}
__attribute__((destructor)) static void report_cost(void) {
    if (layout_updates) fprintf(stderr,
        "layout_boundary updates=%llu repeats=%llu buffer_updates=%llu buffer_repeats=%llu\n",
        layout_updates, layout_repeats, buffer_updates, buffer_repeats);
}
