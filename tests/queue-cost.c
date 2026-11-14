/* Count real worker-side query boundaries; never replace driver results. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

static SDL_threadID producer, query_thread;
static void *(*lookup)(const char *);
static PFNGLGETUNIFORMLOCATIONPROC location;
static PFNGLSAMPLERPARAMETERFVPROC parameter;
static __typeof__(&glTexSubImage2D) image;
static PFNGLCOMPRESSEDTEXSUBIMAGE2DPROC compressed;
static __typeof__(&glReadPixels) pixels;
static __typeof__(&glDeleteTextures) delete_textures;
static PFNGLDELETEBUFFERSPROC delete_buffers;
static unsigned locations, reads, borders, images, blocks, textures_deleted, buffers_deleted;
static GLint count_location(GLuint program, const GLchar *name) {
    if (SDL_ThreadID() != producer) { locations++; query_thread=SDL_ThreadID(); }
    return location(program,name);
}
static void count_pixels(GLint x,GLint y,GLsizei w,GLsizei h,GLenum format,GLenum type,void *data) {
    /* Earlier context-capability probe has no program queries of its own. */
    reads += query_thread && SDL_ThreadID() == query_thread;
    pixels(x,y,w,h,format,type,data);
}
static void count_parameter(GLuint sampler,GLenum name,const GLfloat *value) {
    borders += name == GL_TEXTURE_BORDER_COLOR;
    parameter(sampler,name,value);
}
static void count_image(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,
                        GLenum format,GLenum type,const void *data) {
    images++; image(target,level,x,y,w,h,format,type,data);
}
static void count_compressed(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,
                             GLenum format,GLsizei size,const void *data) {
    blocks++; compressed(target,level,x,y,w,h,format,size,data);
}
static void count_delete_textures(GLsizei n,const GLuint *names) {
    textures_deleted += n > 0 ? (unsigned)n : 0;
    delete_textures(n,names);
}
static void count_delete_buffers(GLsizei n,const GLuint *names) {
    buffers_deleted += n > 0 ? (unsigned)n : 0;
    delete_buffers(n,names);
}
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) { producer=SDL_ThreadID(); lookup=dlsym(RTLD_NEXT,"SDL_GL_GetProcAddress"); }
    void *function=lookup(name);
    if (!function) return NULL;
    if (!strcmp(name,"glGetUniformLocation")) { location=function; return count_location; }
    if (!strcmp(name,"glReadPixels")) { pixels=function; return count_pixels; }
    if (!strcmp(name,"glSamplerParameterfv")) { parameter=function; return count_parameter; }
    if (!strcmp(name,"glTexSubImage2D")) { image=function; return count_image; }
    if (!strcmp(name,"glCompressedTexSubImage2D")) { compressed=function; return count_compressed; }
    if (!strcmp(name,"glDeleteTextures")) { delete_textures=function; return count_delete_textures; }
    if (!strcmp(name,"glDeleteBuffers")) { delete_buffers=function; return count_delete_buffers; }
    return function;
}
__attribute__((destructor)) static void report(void) {
    if (!locations && !reads) return;
    fprintf(stderr,"query_boundary locations=%u reads=%u borders=%u images=%u blocks=%u\n",
            locations,reads,borders,images,blocks);
    fprintf(stderr,"delete_boundary textures=%u buffers=%u\n",textures_deleted,buffers_deleted);
}
