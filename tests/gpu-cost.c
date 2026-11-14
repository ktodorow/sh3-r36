/* Observe actual timer-query results and ordering; forward driver work. */
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *(*lookup)(const char *);
static PFNGLBEGINQUERYPROC begin_query;
static PFNGLENDQUERYPROC end_query;
static PFNGLGETQUERYOBJECTUIVPROC get_query;
static PFNGLGETQUERYOBJECTUI64VPROC get_result;
static __typeof__(&glFinish) finish;
static SDL_threadID producer;
static unsigned begins, ends, reads, premature, main_calls, finishes;
static struct { GLuint id; int available; } ready[64];
static unsigned ready_count;
static GLuint64 nanoseconds;
static unsigned slot(GLuint id) {
    for (unsigned i=0;i<ready_count;i++) if (ready[i].id==id) return i;
    if (ready_count==64) abort();
    ready[ready_count].id=id;
    return ready_count++;
}
static void observe_begin(GLenum target, GLuint id) {
    begins++; main_calls += SDL_ThreadID() == producer;
    ready[slot(id)].available=0;
    begin_query(target,id);
}
static void observe_end(GLenum target) { ends++; end_query(target); }
static void observe_query(GLuint id,GLenum name,GLuint *value) {
    get_query(id,name,value);
    if (name == GL_QUERY_RESULT_AVAILABLE) ready[slot(id)].available=*value;
}
static void observe_result(GLuint id,GLenum name,GLuint64 *value) {
    premature += !ready[slot(id)].available;
    get_result(id,name,value);
    if (name == GL_QUERY_RESULT) { reads++; nanoseconds += *value; }
}
static void observe_finish(void) { finishes++; finish(); }
void *SDL_GL_GetProcAddress(const char *name) {
    if (!lookup) { producer=SDL_ThreadID(); lookup=dlsym(RTLD_NEXT,"SDL_GL_GetProcAddress"); }
    if (getenv("SH3_TEST_NO_GPU_TIMER") &&
        (!strcmp(name,"glGetQueryObjectui64v") || !strcmp(name,"glGetQueryObjectui64vEXT")))
        return NULL;
    void *function=lookup(name);
    if (!function) return NULL;
    if (!strcmp(name,"glBeginQuery") || !strcmp(name,"glBeginQueryEXT")) {
        begin_query=function; return observe_begin;
    }
    if (!strcmp(name,"glEndQuery") || !strcmp(name,"glEndQueryEXT")) {
        end_query=function; return observe_end;
    }
    if (!strcmp(name,"glGetQueryObjectuiv") || !strcmp(name,"glGetQueryObjectuivEXT")) {
        get_query=function; return observe_query;
    }
    if (!strcmp(name,"glGetQueryObjectui64v") || !strcmp(name,"glGetQueryObjectui64vEXT")) {
        get_result=function; return observe_result;
    }
    if (!strcmp(name,"glFinish")) { finish=function; return observe_finish; }
    return function;
}
__attribute__((destructor)) static void report(void) {
    if (!begins && !reads) return;
    fprintf(stderr,"gpu_boundary begins=%u ends=%u reads=%u premature=%u main=%u finishes=%u ns=%llu\n",
            begins,ends,reads,premature,main_calls,finishes,(unsigned long long)nanoseconds);
}
