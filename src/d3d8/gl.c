#define GL_LOADER_IMPL
#include "gl.h"
#include "../runtime/rt.h"

#define GL_DEFINE(type, name) type p_##name;
GL_FUNCS(GL_DEFINE)

int gl_es, gl_clip_emulated;
static void (*clear_depth_f)(GLfloat);
static void (*depth_range_f)(GLfloat, GLfloat);
static void clear_depth(GLdouble depth) { clear_depth_f(depth); }
static void depth_range(GLdouble near, GLdouble far) { depth_range_f(near, far); }

/* Actual context state: Clear, Present and resource helpers use these entry
 * points too. Unknown capabilities retain ordinary GL validation/behavior. */
static __typeof__(&glEnable) driver_enable;
static __typeof__(&glDisable) driver_disable;
static uint8_t cap_valid[6], cap_enabled[6];
static int capability_index(GLenum cap) {
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
static void set_capability(GLenum cap, int enabled) {
    int i = capability_index(cap);
    if (i >= 0 && cap_valid[i] && cap_enabled[i] == enabled) return;
    if (enabled) driver_enable(cap); else driver_disable(cap);
    if (i >= 0) { cap_enabled[i] = enabled; cap_valid[i] = 1; }
}
static void cached_enable(GLenum cap) { set_capability(cap, 1); }
static void cached_disable(GLenum cap) { set_capability(cap, 0); }

/* All programs are linked here before use, and remain alive for this context. */
static PFNGLUSEPROGRAMPROC driver_use_program;
static GLuint current_program;
static uint8_t program_valid;
static void cached_use_program(GLuint program) {
    if (program_valid && current_program == program) return;
    driver_use_program(program);
    current_program = program; program_valid = 1;
}

static PFNGLBINDBUFFERPROC driver_bind_buffer;
static PFNGLDELETEBUFFERSPROC driver_delete_buffers;
static PFNGLBINDVERTEXARRAYPROC driver_bind_vertex_array;
static PFNGLVERTEXATTRIBPOINTERPROC driver_attrib_pointer;
static GLuint array_buffer;
static uint8_t array_buffer_valid;
static struct {
    GLuint buffer;
    GLint size;
    GLenum type;
    GLsizei stride;
    const void *offset;
    GLboolean normalized;
    uint8_t valid;
} attrib_state[16];
static void cached_bind_buffer(GLenum target, GLuint buffer) {
    if (target == GL_ARRAY_BUFFER && array_buffer_valid && array_buffer == buffer) return;
    driver_bind_buffer(target, buffer);
    if (target == GL_ARRAY_BUFFER) { array_buffer = buffer; array_buffer_valid = 1; }
}
static void cached_delete_buffers(GLsizei n, const GLuint *buffers) {
    /* Deletion can reset bindings/attribute sources; names may later be reused. */
    memset(attrib_state, 0, sizeof attrib_state);
    array_buffer_valid = 0;
    driver_delete_buffers(n, buffers);
}
static void cached_bind_vertex_array(GLuint vao) {
    /* Attribute layout and element binding belong to VAO, ARRAY_BUFFER does not. */
    memset(attrib_state, 0, sizeof attrib_state);
    driver_bind_vertex_array(vao);
}
static void cached_attrib_pointer(GLuint i, GLint size, GLenum type, GLboolean normalized,
                                  GLsizei stride, const void *offset) {
    int cacheable = i < 16 && array_buffer_valid && array_buffer && stride >= 0 &&
        ((size >= 1 && size <= 4) || (!gl_es && size == GL_BGRA)) &&
        (type == GL_FLOAT || type == GL_UNSIGNED_BYTE || type == GL_SHORT);
    if (cacheable && attrib_state[i].valid && attrib_state[i].buffer == array_buffer &&
        attrib_state[i].size == size && attrib_state[i].type == type &&
        attrib_state[i].normalized == normalized && attrib_state[i].stride == stride &&
        attrib_state[i].offset == offset) return;
    driver_attrib_pointer(i, size, type, normalized, stride, offset);
    if (cacheable) {
        attrib_state[i].buffer = array_buffer; attrib_state[i].size = size; attrib_state[i].type = type;
        attrib_state[i].normalized = normalized; attrib_state[i].stride = stride;
        attrib_state[i].offset = offset; attrib_state[i].valid = 1;
    } else if (i < 16) attrib_state[i].valid = 0;
}

static __typeof__(&glViewport) driver_viewport;
static __typeof__(&glDepthRange) driver_depth_range;
static __typeof__(&glDepthMask) driver_depth_mask;
static __typeof__(&glColorMask) driver_color_mask;
static __typeof__(&glDepthFunc) driver_depth_func;
static struct {
    GLint viewport[4];
    GLdouble depth_range[2];
    GLboolean depth_mask, color_mask[4];
    GLenum depth_func;
    uint8_t viewport_valid, depth_range_valid, depth_mask_valid, color_mask_valid, depth_func_valid;
} raster;
static void cached_viewport(GLint x, GLint y, GLsizei w, GLsizei h) {
    const GLint value[] = {x, y, w, h};
    if (w < 0 || h < 0) { driver_viewport(x, y, w, h); return; }
    if (raster.viewport_valid && !memcmp(raster.viewport, value, sizeof value)) return;
    driver_viewport(x, y, w, h);
    memcpy(raster.viewport, value, sizeof value); raster.viewport_valid = 1;
}
static void cached_depth_range(GLdouble near, GLdouble far) {
    const GLdouble value[] = {near, far};
    if (raster.depth_range_valid && !memcmp(raster.depth_range, value, sizeof value)) return;
    driver_depth_range(near, far);
    memcpy(raster.depth_range, value, sizeof value); raster.depth_range_valid = 1;
}
static void cached_depth_mask(GLboolean value) {
    if (raster.depth_mask_valid && raster.depth_mask == value) return;
    driver_depth_mask(value);
    raster.depth_mask = value; raster.depth_mask_valid = 1;
}
static void cached_color_mask(GLboolean r, GLboolean g, GLboolean b, GLboolean a) {
    const GLboolean value[] = {r, g, b, a};
    if (raster.color_mask_valid && !memcmp(raster.color_mask, value, sizeof value)) return;
    driver_color_mask(r, g, b, a);
    memcpy(raster.color_mask, value, sizeof value); raster.color_mask_valid = 1;
}
static void cached_depth_func(GLenum value) {
    if (value < GL_NEVER || value > GL_ALWAYS) { driver_depth_func(value); return; }
    if (raster.depth_func_valid && raster.depth_func == value) return;
    driver_depth_func(value);
    raster.depth_func = value; raster.depth_func_valid = 1;
}

int gl_has_extension(const char *name) {
    GLint count = 0;
    p_glGetIntegerv(GL_NUM_EXTENSIONS, &count);
    for (int i = 0; i < count; i++)
        if (!strcmp((const char *)p_glGetStringi(GL_EXTENSIONS, i), name)) return 1;
    return 0;
}

void gl_prepare_context(void) {
    const char *backend = getenv("SH3_GL_BACKEND");
#ifdef __aarch64__
    int es = !backend || strcmp(backend, "desktop");
#else
    int es = backend && !strcmp(backend, "gles");
#endif
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, es ? SDL_GL_CONTEXT_PROFILE_ES : SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, es ? 3 : 4);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, es ? 2 : 5);
}

void gl_load(void) {
    const GLubyte *(*string)(GLenum) = SDL_GL_GetProcAddress("glGetString");
    gl_es = string && strstr((const char *)string(GL_VERSION), "OpenGL ES") != NULL;
#define GL_LOAD_FN(type, name) do { \
    p_##name = (type)SDL_GL_GetProcAddress(#name); \
    int desktop = !strcmp(#name, "glClearDepth") || !strcmp(#name, "glDepthRange") || \
                  !strcmp(#name, "glPolygonMode") || !strcmp(#name, "glClipControl"); \
    if (!p_##name && !desktop && strcmp(#name, "glDrawElementsBaseVertex")) rt_fatal("missing GL function " #name); \
} while (0);
    GL_FUNCS(GL_LOAD_FN)
    /* Loader owns one current context; reload never inherits prior state. */
    memset(cap_valid, 0, sizeof cap_valid);
    driver_enable = p_glEnable; driver_disable = p_glDisable;
    p_glEnable = cached_enable; p_glDisable = cached_disable;
    program_valid = 0;
    driver_use_program = p_glUseProgram; p_glUseProgram = cached_use_program;
    array_buffer_valid = 0;
    memset(attrib_state, 0, sizeof attrib_state);
    driver_bind_buffer = p_glBindBuffer; p_glBindBuffer = cached_bind_buffer;
    driver_delete_buffers = p_glDeleteBuffers; p_glDeleteBuffers = cached_delete_buffers;
    driver_bind_vertex_array = p_glBindVertexArray; p_glBindVertexArray = cached_bind_vertex_array;
    driver_attrib_pointer = p_glVertexAttribPointer; p_glVertexAttribPointer = cached_attrib_pointer;
    if (gl_es) {
        clear_depth_f = SDL_GL_GetProcAddress("glClearDepthf");
        depth_range_f = SDL_GL_GetProcAddress("glDepthRangef");
        if (!clear_depth_f || !depth_range_f) rt_fatal("missing GLES depth functions");
        p_glClearDepth = clear_depth;
        p_glDepthRange = depth_range;
    }
    memset(&raster, 0, sizeof raster);
    driver_viewport = p_glViewport; p_glViewport = cached_viewport;
    driver_depth_range = p_glDepthRange; p_glDepthRange = cached_depth_range;
    driver_depth_mask = p_glDepthMask; p_glDepthMask = cached_depth_mask;
    driver_color_mask = p_glColorMask; p_glColorMask = cached_color_mask;
    driver_depth_func = p_glDepthFunc; p_glDepthFunc = cached_depth_func;
    GLint major = 0, minor = 0;
    p_glGetIntegerv(GL_MAJOR_VERSION, &major); p_glGetIntegerv(GL_MINOR_VERSION, &minor);
    const char *base = "core";
    if (gl_es && (major < 3 || (major == 3 && minor < 2))) {
        if (gl_has_extension("GL_OES_draw_elements_base_vertex")) {
            p_glDrawElementsBaseVertex = SDL_GL_GetProcAddress("glDrawElementsBaseVertexOES"); base = "OES";
        } else if (gl_has_extension("GL_EXT_draw_elements_base_vertex")) {
            p_glDrawElementsBaseVertex = SDL_GL_GetProcAddress("glDrawElementsBaseVertexEXT"); base = "EXT";
        } else p_glDrawElementsBaseVertex = NULL;
    }
    if (!p_glDrawElementsBaseVertex) rt_fatal("required indexed base-vertex operation unavailable");
    gl_clip_emulated = gl_es || (!gl_has_extension("GL_ARB_clip_control") && (major < 4 || (major == 4 && minor < 5)));
    if (!gl_clip_emulated) {
        if (!p_glClipControl) rt_fatal("missing supported glClipControl entry point");
        p_glClipControl(GL_UPPER_LEFT, GL_ZERO_TO_ONE);
    }
    printf("gl_backend=%s\nclip_coordinates=%s\nbase_vertex_api=%s\n", gl_es ? "gles" : "desktop",
           gl_clip_emulated ? "shader-y-invert-z-remap" : "clip-control", base);
}
