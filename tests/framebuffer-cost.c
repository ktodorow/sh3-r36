/* Real framebuffer boundary observation; no replacement rendering or statuses. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Attachment { GLenum target; GLuint texture; GLint level; int valid; };
struct Framebuffer {
    GLuint id;
    struct Attachment color, depth;
    unsigned generation, checked_generation, checked_storage;
    int checked;
};
static struct Framebuffer framebuffers[512];
static GLuint draw_framebuffer, read_framebuffer;
static unsigned storage;
static unsigned long long attaches, attach_repeats, checks, check_repeats;
static void *(*lookup)(const char *);
static PFNGLBINDFRAMEBUFFERPROC bind_fb;
static PFNGLFRAMEBUFFERTEXTURE2DPROC attach_fb;
static PFNGLCHECKFRAMEBUFFERSTATUSPROC check_fb;
static PFNGLDELETEFRAMEBUFFERSPROC delete_fb;
static void (*image)(GLenum,GLint,GLint,GLsizei,GLsizei,GLint,GLenum,GLenum,const void *);
static void (*delete_tex)(GLsizei,const GLuint *);

static struct Framebuffer *state(GLuint id) {
    if (!id) abort();
    for (unsigned i=0;i<512;i++) if (framebuffers[i].id == id) return &framebuffers[i];
    for (unsigned i=0;i<512;i++) if (!framebuffers[i].id) {
        framebuffers[i].id = id; return &framebuffers[i];
    }
    abort();
}
static void observe_bind(GLenum target, GLuint id) {
    if (target==GL_FRAMEBUFFER || target==GL_DRAW_FRAMEBUFFER) draw_framebuffer=id;
    if (target==GL_FRAMEBUFFER || target==GL_READ_FRAMEBUFFER) read_framebuffer=id;
    bind_fb(target,id);
}
static void observe_attach(GLenum target, GLenum attachment, GLenum texture_target, GLuint tex, GLint level) {
    struct Framebuffer *fb=state(target==GL_READ_FRAMEBUFFER ? read_framebuffer : draw_framebuffer);
    struct Attachment *a=attachment==GL_COLOR_ATTACHMENT0 ? &fb->color : &fb->depth;
    attaches++;
    if (a->valid && a->target==texture_target && a->texture==tex && a->level==level) attach_repeats++;
    else fb->generation++;
    *a=(struct Attachment){texture_target,tex,level,1};
    attach_fb(target,attachment,texture_target,tex,level);
}
static GLenum observe_check(GLenum target) {
    struct Framebuffer *fb=state(target==GL_READ_FRAMEBUFFER ? read_framebuffer : draw_framebuffer);
    checks++;
    if (fb->checked && fb->checked_generation==fb->generation && fb->checked_storage==storage) check_repeats++;
    GLenum result=check_fb(target);
    fb->checked=1; fb->checked_generation=fb->generation; fb->checked_storage=storage;
    return result;
}
static void observe_delete(GLsizei n, const GLuint *ids) {
    for (int i=0;i<n;i++) for (unsigned j=0;j<512;j++)
        if (framebuffers[j].id==ids[i]) memset(&framebuffers[j],0,sizeof framebuffers[j]);
    delete_fb(n,ids);
}
static void observe_image(GLenum target,GLint level,GLint format,GLsizei w,GLsizei h,GLint border,
                          GLenum f,GLenum type,const void *pixels) {
    storage++; image(target,level,format,w,h,border,f,type,pixels);
}
static void observe_delete_tex(GLsizei n,const GLuint *ids) {
    storage++;
    for (int i=0;i<n;i++) for (unsigned j=0;j<512;j++) {
        struct Framebuffer *fb=&framebuffers[j];
        if (fb->color.texture==ids[i]) fb->color.valid=0;
        if (fb->depth.texture==ids[i]) fb->depth.valid=0;
    }
    delete_tex(n,ids);
}
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) lookup=dlsym(RTLD_NEXT,"SDL_GL_GetProcAddress");
    void *function=lookup(name);
    if (!function) return NULL;
#define WRAP(gl, driver, wrapper) if (!strcmp(name,#gl)) { driver=function; return wrapper; }
    WRAP(glBindFramebuffer,bind_fb,observe_bind)
    WRAP(glFramebufferTexture2D,attach_fb,observe_attach)
    WRAP(glCheckFramebufferStatus,check_fb,observe_check)
    WRAP(glDeleteFramebuffers,delete_fb,observe_delete)
    WRAP(glTexImage2D,image,observe_image)
    WRAP(glDeleteTextures,delete_tex,observe_delete_tex)
#undef WRAP
    return function;
}
__attribute__((destructor)) static void report(void) {
    if (checks) fprintf(stderr,"framebuffer_boundary attaches=%llu attach_repeats=%llu checks=%llu check_repeats=%llu\n",
                        attaches,attach_repeats,checks,check_repeats);
}
