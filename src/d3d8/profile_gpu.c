#define GL_LOADER_IMPL
#include "gl.h"
#include "profile_gpu.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Core and EXT query tokens have identical values. Disjoint is GLES-only. */
#define GPU_DISJOINT 0x8FBB
enum { QUERY_COUNT=8 };
typedef struct Query {
    GLuint id;
    int pending, invalid;
    unsigned serial;
    ProfileSwap frame;
    uint64_t elapsed;
} Query;
static Query queries[QUERY_COUNT], *current;
static FILE *report;
static int checked, disjoint, frame_skipped;
static unsigned serial, skipped, discarded;
static PFNGLGENQUERIESPROC gen;
static PFNGLDELETEQUERIESPROC destroy;
static PFNGLBEGINQUERYPROC begin;
static PFNGLENDQUERYPROC end;
static PFNGLGETQUERYIVPROC target;
static PFNGLGETQUERYOBJECTUIVPROC available;
static PFNGLGETQUERYOBJECTUI64VPROC result;
static __typeof__(&glGetIntegerv) integer;
static __typeof__(&glGetError) error;

static int has_disjoint(void) {
    PFNGLGETSTRINGIPROC string = SDL_GL_GetProcAddress("glGetStringi");
    GLint count=0;
    integer(GL_NUM_EXTENSIONS,&count);
    if (string) for (GLint i=0;i<count;i++)
        if (!strcmp((const char *)string(GL_EXTENSIONS,i),"GL_EXT_disjoint_timer_query")) return 1;
    return 0;
}
static void initialize(void) {
    checked=1;
    const char *explicit=getenv("SH3_GPU_PROFILE"), *base=getenv("SH3_PROFILE");
    if (!explicit || !*explicit || !strcmp(explicit,"0")) return;
    __typeof__(&glGetString) string=SDL_GL_GetProcAddress("glGetString");
    integer=SDL_GL_GetProcAddress("glGetIntegerv");
    error=SDL_GL_GetProcAddress("glGetError");
    int es=string && strstr((const char *)string(GL_VERSION),"OpenGL ES") != NULL;
    disjoint=es;
    if (!integer || !error || (es && !has_disjoint())) {
        puts("gpu_profile=unavailable reason=extension"); return;
    }
#define LOAD(field,name) field=SDL_GL_GetProcAddress(es ? name "EXT" : name)
    LOAD(gen,"glGenQueries"); LOAD(destroy,"glDeleteQueries");
    LOAD(begin,"glBeginQuery"); LOAD(end,"glEndQuery");
    LOAD(target,"glGetQueryiv"); LOAD(available,"glGetQueryObjectuiv");
    LOAD(result,"glGetQueryObjectui64v");
#undef LOAD
    if (!gen || !destroy || !begin || !end || !target || !available || !result) {
        puts("gpu_profile=unavailable reason=entry-points"); return;
    }
    GLint bits=0;
    target(GL_TIME_ELAPSED,GL_QUERY_COUNTER_BITS,&bits);
    if (!bits) { puts("gpu_profile=unavailable reason=counter-bits"); return; }
    char *name=NULL;
    if (!strcmp(explicit,"1")) {
        if (base && *base) {
            name=malloc(strlen(base)+sizeof ".gpu.csv");
            if (name) { strcpy(name,base); strcat(name,".gpu.csv"); }
        }
    } else name=strdup(explicit);
    if (name) { report=fopen(name,"w"); free(name); }
    if (!report) { puts("gpu_profile=unavailable reason=report"); return; }
    static char buffer[65536];
    setvbuf(report,buffer,_IOFBF,sizeof buffer);
    fputs("frame,elapsed_ms,gpu_ms,room,internal_w,internal_h\n",report);
    GLuint ids[QUERY_COUNT]={0};
    gen(QUERY_COUNT,ids);
    for (unsigned i=0;i<QUERY_COUNT;i++) queries[i].id=ids[i];
    if (disjoint) { GLint ignored; integer(GPU_DISJOINT,&ignored); }
    if (error()!=GL_NO_ERROR) {
        puts("gpu_profile=unavailable reason=query-setup");
        fclose(report); report=NULL; return;
    }
    printf("gpu_profile=enabled counter_bits=%d queries=%d delayed_frames=3\n",bits,QUERY_COUNT);
}
static void reject_disjoint(void) {
    if (!disjoint) return;
    GLint occurred=0;
    integer(GPU_DISJOINT,&occurred);
    if (occurred) for (unsigned i=0;i<QUERY_COUNT;i++)
        if (queries[i].pending) queries[i].invalid=1;
}
static void collect(int stopping) {
    reject_disjoint();
    GLuint ready[QUERY_COUNT]={0};
    GLuint64 times[QUERY_COUNT]={0};
    for (unsigned i=0;i<QUERY_COUNT;i++) {
        Query *q=&queries[i];
        if (!q->pending || (!stopping && serial-q->serial<3)) continue;
        available(q->id,GL_QUERY_RESULT_AVAILABLE,&ready[i]);
        if (ready[i] && !q->invalid) result(q->id,GL_QUERY_RESULT,&times[i]);
    }
    /* Reject results invalidated during polling, including earlier pending work. */
    reject_disjoint();
    for (unsigned count=0;count<QUERY_COUNT;count++) {
        unsigned i=QUERY_COUNT;
        for (unsigned j=0;j<QUERY_COUNT;j++) if (ready[j] &&
                (i==QUERY_COUNT || queries[j].serial<queries[i].serial)) i=j;
        if (i==QUERY_COUNT) break;
        Query *q=&queries[i];
        if (q->invalid) discarded++;
        else fprintf(report,"%u,%llu,%.6f,%u,%u,%u\n",
                q->frame.enabled ? (unsigned)q->frame.frame : q->serial,
                (unsigned long long)q->elapsed,times[i]/1000000.0,
                q->frame.room,q->frame.width,q->frame.height);
        q->pending=0; q->invalid=0;
        ready[i]=0;
    }
    if (ferror(report)) {
        puts("gpu_profile=failed reason=write");
        fclose(report); report=NULL;
    }
}
void profile_gpu_begin(void) {
    if (!checked) initialize();
    if (!report || current || frame_skipped) return;
    collect(0);
    if (!report) return;
    for (unsigned i=0;i<QUERY_COUNT;i++) if (!queries[i].pending) {
        current=&queries[i];
        begin(GL_TIME_ELAPSED,current->id);
        if (!serial && error()!=GL_NO_ERROR) {
            puts("gpu_profile=unavailable reason=query-begin");
            current=NULL; fclose(report); report=NULL;
        }
        return;
    }
    skipped++; frame_skipped=1;
}
void profile_gpu_end(ProfileSwap frame) {
    if (!report) return;
    serial++;
    frame_skipped=0;
    if (!current) return;
    end(GL_TIME_ELAPSED);
    current->serial=serial;
    current->frame=frame;
    current->elapsed=SDL_GetTicks64();
    current->pending=1;
    current=NULL;
}
void profile_gpu_stop(void) {
    if (current) { end(GL_TIME_ELAPSED); current=NULL; }
    if (report) { collect(1); if (report) { fclose(report); report=NULL; } }
    if (queries[0].id) {
        GLuint ids[QUERY_COUNT];
        for (unsigned i=0;i<QUERY_COUNT;i++) ids[i]=queries[i].id;
        destroy(QUERY_COUNT,ids);
        printf("gpu_profile=stopped skipped=%u disjoint_discarded=%u\n",skipped,discarded);
    }
    memset(queries,0,sizeof queries);
    checked=disjoint=frame_skipped=0; serial=skipped=discarded=0;
}
