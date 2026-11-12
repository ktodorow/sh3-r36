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
    if (gl_es) {
        clear_depth_f = SDL_GL_GetProcAddress("glClearDepthf");
        depth_range_f = SDL_GL_GetProcAddress("glDepthRangef");
        if (!clear_depth_f || !depth_range_f) rt_fatal("missing GLES depth functions");
        p_glClearDepth = clear_depth;
        p_glDepthRange = depth_range;
    }
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
