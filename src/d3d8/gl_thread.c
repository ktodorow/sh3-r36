/* One context owner, ordered commands, at most one frame ahead. Native renderer
 * supplies VBO/EBO offsets, never client-side vertex/index arrays. Output APIs
 * and shader inputs remain synchronous; transient upload data is copied. */
#define GL_LOADER_IMPL
#include "gl.h"
#include "profile.h"
#include "profile_gpu.h"
#include "../runtime/rt.h"
#include <stdint.h>

#define DRIVER(type, name) static type driver_##name;
GL_FUNCS(DRIVER)
#undef DRIVER

typedef void (*Run)(const void *);
typedef struct Command { Run run; size_t bytes; } Command;
typedef struct Chunk {
    unsigned char *data;
    size_t used, capacity;
    uint64_t serial;
    int state;
} Chunk;
enum { FREE, BUILDING, READY, RUNNING };
static Chunk chunks[3], *building;
static unsigned write_slot, read_slot;
static SDL_mutex *mutex;
static SDL_cond *condition;
static SDL_Thread *worker;
static SDL_GLContext context;
static SDL_threadID producer;
static uint64_t submitted_jobs, completed_jobs, submitted_frames, completed_frames;
static int active, stopping, started, start_failed;
typedef struct SyncCost { const char *api; uint64_t calls, ticks; } SyncCost;
#define COST(type, name) static SyncCost cost_##name = {#name, 0, 0};
GL_FUNCS(COST)
#undef COST
static int queue_stats;
static GLint unpack_alignment, unpack_row_length, unpack_skip_rows, unpack_skip_pixels, unpack_buffer;

SDL_GLContext gl_current_context(void) {
    return active ? context : SDL_GL_GetCurrentContext();
}

static int render_worker(void *unused) {
    (void)unused;
    int failed = SDL_GL_MakeCurrent(rt_window, context) != 0;
    SDL_LockMutex(mutex);
    start_failed = failed; started = 1;
    SDL_CondBroadcast(condition);
    for (;;) {
        Chunk *chunk = &chunks[read_slot];
        while (chunk->state != READY && !stopping) SDL_CondWait(condition, mutex);
        if (chunk->state != READY) break;
        chunk->state = RUNNING;
        SDL_UnlockMutex(mutex);
        profile_gpu_begin();
        for (size_t offset = 0; offset < chunk->used;) {
            const Command *command = (const Command *)(chunk->data + offset);
            command->run(command + 1);
            offset += command->bytes;
        }
        SDL_LockMutex(mutex);
        completed_jobs = chunk->serial;
        chunk->state = FREE;
        read_slot = (read_slot + 1) % 3;
        SDL_CondBroadcast(condition);
    }
    SDL_UnlockMutex(mutex);
    profile_gpu_stop();
    if (!failed && SDL_GL_MakeCurrent(rt_window, NULL)) return 1;
    return failed;
}

static uint64_t publish(void) {
    if (!building || !building->used) return submitted_jobs;
    SDL_LockMutex(mutex);
    building->serial = ++submitted_jobs;
    building->state = READY;
    building = NULL;
    write_slot = (write_slot + 1) % 3;
    SDL_CondBroadcast(condition);
    SDL_UnlockMutex(mutex);
    return submitted_jobs;
}

static void wait_job(uint64_t serial) {
    SDL_LockMutex(mutex);
    while (completed_jobs < serial) SDL_CondWait(condition, mutex);
    SDL_UnlockMutex(mutex);
}

static void *record(Run run, size_t size) {
    if (SDL_ThreadID() != producer) rt_fatal("GL queue called from non-producer thread");
    if (size > SIZE_MAX - sizeof(Command) - 15) rt_fatal("GL command size overflow");
    size_t bytes = (sizeof(Command) + size + 15) & ~(size_t)15;
    if (building && bytes > building->capacity - building->used) publish();
    if (!building) {
        SDL_LockMutex(mutex);
        building = &chunks[write_slot];
        while (building->state != FREE) SDL_CondWait(condition, mutex);
        building->state = BUILDING;
        SDL_UnlockMutex(mutex);
        building->used = 0;
        if (building->capacity < bytes) {
            size_t capacity = bytes > 8u*1024*1024 ? bytes : 8u*1024*1024;
            unsigned char *data = realloc(building->data, capacity);
            if (!data) rt_fatal("GL command allocation failed");
            building->data = data; building->capacity = capacity;
        }
    }
    Command *command = (Command *)(building->data + building->used);
    *command = (Command){run, bytes};
    building->used += bytes;
    return command + 1;
}

typedef struct Sync { void (*run)(void *); void *data; } Sync;
static void run_sync(const void *data) {
    const Sync *call = data;
    call->run(call->data);
}
static void synchronize(void (*run)(void *), void *data, SyncCost *cost) {
    uint64_t start = queue_stats ? SDL_GetPerformanceCounter() : 0;
    *(Sync *)record(run_sync, sizeof(Sync)) = (Sync){run, data};
    wait_job(publish());
    if (queue_stats) { cost->calls++; cost->ticks += SDL_GetPerformanceCounter() - start; }
}

#define UNPACK(...) __VA_ARGS__
#define ASYNC(name, params, fields, initial, arguments) \
    typedef struct { UNPACK fields } Args_##name; \
    static void run_##name(const void *data) { \
        const Args_##name *c = data; driver_##name arguments; \
    } \
    static void queued_##name params { \
        *(Args_##name *)record(run_##name, sizeof(Args_##name)) = (Args_##name){UNPACK initial}; \
    }
#define SYNC_VOID(name, params, fields, initial, arguments) \
    typedef struct { UNPACK fields } Args_##name; \
    static void run_##name(void *data) { Args_##name *c = data; driver_##name arguments; } \
    static void queued_##name params { \
        Args_##name c = {UNPACK initial}; synchronize(run_##name, &c, &cost_##name); \
    }
#define SYNC_RESULT(type, name, params, fields, initial, arguments) \
    typedef struct { UNPACK fields type result; } Args_##name; \
    static void run_##name(void *data) { Args_##name *c = data; c->result = driver_##name arguments; } \
    static type queued_##name params { \
        Args_##name c = {UNPACK initial}; synchronize(run_##name, &c, &cost_##name); return c.result; \
    }

ASYNC(glBindTexture,(GLenum target,GLuint texture),(GLenum target; GLuint texture;),(target,texture),(c->target,c->texture))
ASYNC(glClear,(GLbitfield mask),(GLbitfield mask;),(mask),(c->mask))
ASYNC(glClearColor,(GLfloat r,GLfloat g,GLfloat b,GLfloat a),(GLfloat r,g,b,a;),(r,g,b,a),(c->r,c->g,c->b,c->a))
ASYNC(glClearDepth,(GLdouble depth),(GLdouble depth;),(depth),(c->depth))
ASYNC(glClearStencil,(GLint stencil),(GLint stencil;),(stencil),(c->stencil))
ASYNC(glColorMask,(GLboolean r,GLboolean g,GLboolean b,GLboolean a),(GLboolean r,g,b,a;),(r,g,b,a),(c->r,c->g,c->b,c->a))
ASYNC(glCullFace,(GLenum mode),(GLenum mode;),(mode),(c->mode))
ASYNC(glDepthFunc,(GLenum function),(GLenum function;),(function),(c->function))
ASYNC(glDepthMask,(GLboolean flag),(GLboolean flag;),(flag),(c->flag))
ASYNC(glDepthRange,(GLdouble near,GLdouble far),(GLdouble near,far;),(near,far),(c->near,c->far))
ASYNC(glDisable,(GLenum cap),(GLenum cap;),(cap),(c->cap))
ASYNC(glDrawArrays,(GLenum mode,GLint first,GLsizei count),(GLenum mode; GLint first; GLsizei count;),(mode,first,count),(c->mode,c->first,c->count))
ASYNC(glDrawElements,(GLenum mode,GLsizei count,GLenum type,const void *offset),(GLenum mode; GLsizei count; GLenum type; const void *offset;),(mode,count,type,offset),(c->mode,c->count,c->type,c->offset))
ASYNC(glEnable,(GLenum cap),(GLenum cap;),(cap),(c->cap))
ASYNC(glFrontFace,(GLenum mode),(GLenum mode;),(mode),(c->mode))
ASYNC(glPolygonMode,(GLenum face,GLenum mode),(GLenum face,mode;),(face,mode),(c->face,c->mode))
ASYNC(glPolygonOffset,(GLfloat factor,GLfloat units),(GLfloat factor,units;),(factor,units),(c->factor,c->units))
ASYNC(glScissor,(GLint x,GLint y,GLsizei w,GLsizei h),(GLint x,y; GLsizei w,h;),(x,y,w,h),(c->x,c->y,c->w,c->h))
ASYNC(glStencilFunc,(GLenum function,GLint ref,GLuint mask),(GLenum function; GLint ref; GLuint mask;),(function,ref,mask),(c->function,c->ref,c->mask))
ASYNC(glStencilMask,(GLuint mask),(GLuint mask;),(mask),(c->mask))
ASYNC(glTexParameteri,(GLenum target,GLenum name,GLint value),(GLenum target,name; GLint value;),(target,name,value),(c->target,c->name,c->value))
ASYNC(glViewport,(GLint x,GLint y,GLsizei w,GLsizei h),(GLint x,y; GLsizei w,h;),(x,y,w,h),(c->x,c->y,c->w,c->h))
ASYNC(glClipControl,(GLenum origin,GLenum depth),(GLenum origin,depth;),(origin,depth),(c->origin,c->depth))
ASYNC(glBindVertexArray,(GLuint array),(GLuint array;),(array),(c->array))
ASYNC(glVertexAttribPointer,(GLuint index,GLint size,GLenum type,GLboolean normalized,GLsizei stride,const void *offset),(GLuint index; GLint size; GLenum type; GLboolean normalized; GLsizei stride; const void *offset;),(index,size,type,normalized,stride,offset),(c->index,c->size,c->type,c->normalized,c->stride,c->offset))
ASYNC(glVertexAttribIPointer,(GLuint index,GLint size,GLenum type,GLsizei stride,const void *offset),(GLuint index; GLint size; GLenum type; GLsizei stride; const void *offset;),(index,size,type,stride,offset),(c->index,c->size,c->type,c->stride,c->offset))
ASYNC(glEnableVertexAttribArray,(GLuint index),(GLuint index;),(index),(c->index))
ASYNC(glDisableVertexAttribArray,(GLuint index),(GLuint index;),(index),(c->index))
ASYNC(glVertexAttrib4f,(GLuint index,GLfloat x,GLfloat y,GLfloat z,GLfloat w),(GLuint index; GLfloat x,y,z,w;),(index,x,y,z,w),(c->index,c->x,c->y,c->z,c->w))
ASYNC(glUseProgram,(GLuint program),(GLuint program;),(program),(c->program))
ASYNC(glUniform1i,(GLint location,GLint value),(GLint location,value;),(location,value),(c->location,c->value))
ASYNC(glUniform1f,(GLint location,GLfloat value),(GLint location; GLfloat value;),(location,value),(c->location,c->value))
ASYNC(glUniform2f,(GLint location,GLfloat x,GLfloat y),(GLint location; GLfloat x,y;),(location,x,y),(c->location,c->x,c->y))
ASYNC(glActiveTexture,(GLenum texture),(GLenum texture;),(texture),(c->texture))
ASYNC(glGenerateMipmap,(GLenum target),(GLenum target;),(target),(c->target))
ASYNC(glBindFramebuffer,(GLenum target,GLuint framebuffer),(GLenum target; GLuint framebuffer;),(target,framebuffer),(c->target,c->framebuffer))
ASYNC(glFramebufferTexture2D,(GLenum target,GLenum attachment,GLenum textarget,GLuint texture,GLint level),(GLenum target,attachment,textarget; GLuint texture; GLint level;),(target,attachment,textarget,texture,level),(c->target,c->attachment,c->textarget,c->texture,c->level))
ASYNC(glBlitFramebuffer,(GLint sx0,GLint sy0,GLint sx1,GLint sy1,GLint dx0,GLint dy0,GLint dx1,GLint dy1,GLbitfield mask,GLenum filter),(GLint sx0,sy0,sx1,sy1,dx0,dy0,dx1,dy1; GLbitfield mask; GLenum filter;),(sx0,sy0,sx1,sy1,dx0,dy0,dx1,dy1,mask,filter),(c->sx0,c->sy0,c->sx1,c->sy1,c->dx0,c->dy0,c->dx1,c->dy1,c->mask,c->filter))
ASYNC(glBlendFuncSeparate,(GLenum sr,GLenum dr,GLenum sa,GLenum da),(GLenum sr,dr,sa,da;),(sr,dr,sa,da),(c->sr,c->dr,c->sa,c->da))
ASYNC(glBlendEquation,(GLenum mode),(GLenum mode;),(mode),(c->mode))
ASYNC(glBlendColor,(GLfloat r,GLfloat g,GLfloat b,GLfloat a),(GLfloat r,g,b,a;),(r,g,b,a),(c->r,c->g,c->b,c->a))
ASYNC(glStencilOpSeparate,(GLenum face,GLenum fail,GLenum zfail,GLenum pass),(GLenum face,fail,zfail,pass;),(face,fail,zfail,pass),(c->face,c->fail,c->zfail,c->pass))
ASYNC(glDrawElementsBaseVertex,(GLenum mode,GLsizei count,GLenum type,const void *offset,GLint base),(GLenum mode; GLsizei count; GLenum type; const void *offset; GLint base;),(mode,count,type,offset,base),(c->mode,c->count,c->type,c->offset,c->base))
ASYNC(glBindSampler,(GLuint unit,GLuint sampler),(GLuint unit,sampler;),(unit,sampler),(c->unit,c->sampler))
ASYNC(glSamplerParameteri,(GLuint sampler,GLenum name,GLint value),(GLuint sampler; GLenum name; GLint value;),(sampler,name,value),(c->sampler,c->name,c->value))
ASYNC(glSamplerParameterf,(GLuint sampler,GLenum name,GLfloat value),(GLuint sampler; GLenum name; GLfloat value;),(sampler,name,value),(c->sampler,c->name,c->value))

SYNC_VOID(glGenTextures,(GLsizei n,GLuint *names),(GLsizei n; GLuint *names;),(n,names),(c->n,c->names))
SYNC_RESULT(const GLubyte *,glGetString,(GLenum name),(GLenum name;),(name),(c->name))
SYNC_VOID(glGetIntegerv,(GLenum name,GLint *value),(GLenum name; GLint *value;),(name,value),(c->name,c->value))
SYNC_RESULT(const GLubyte *,glGetStringi,(GLenum name,GLuint index),(GLenum name; GLuint index;),(name,index),(c->name,c->index))
SYNC_VOID(glReadPixels,(GLint x,GLint y,GLsizei w,GLsizei h,GLenum format,GLenum type,void *pixels),(GLint x,y; GLsizei w,h; GLenum format,type; void *pixels;),(x,y,w,h,format,type,pixels),(c->x,c->y,c->w,c->h,c->format,c->type,c->pixels))
SYNC_VOID(glTexImage2D,(GLenum target,GLint level,GLint internal,GLsizei w,GLsizei h,GLint border,GLenum format,GLenum type,const void *pixels),(GLenum target; GLint level,internal; GLsizei w,h; GLint border; GLenum format,type; const void *pixels;),(target,level,internal,w,h,border,format,type,pixels),(c->target,c->level,c->internal,c->w,c->h,c->border,c->format,c->type,c->pixels))
SYNC_VOID(glTexParameteriv,(GLenum target,GLenum name,const GLint *values),(GLenum target,name; const GLint *values;),(target,name,values),(c->target,c->name,c->values))
SYNC_VOID(glGenBuffers,(GLsizei n,GLuint *names),(GLsizei n; GLuint *names;),(n,names),(c->n,c->names))
SYNC_VOID(glGenVertexArrays,(GLsizei n,GLuint *names),(GLsizei n; GLuint *names;),(n,names),(c->n,c->names))
SYNC_RESULT(GLuint,glCreateShader,(GLenum type),(GLenum type;),(type),(c->type))
SYNC_VOID(glShaderSource,(GLuint shader,GLsizei count,const GLchar *const *strings,const GLint *lengths),(GLuint shader; GLsizei count; const GLchar *const *strings; const GLint *lengths;),(shader,count,strings,lengths),(c->shader,c->count,c->strings,c->lengths))
SYNC_VOID(glCompileShader,(GLuint shader),(GLuint shader;),(shader),(c->shader))
SYNC_VOID(glGetShaderiv,(GLuint shader,GLenum name,GLint *value),(GLuint shader; GLenum name; GLint *value;),(shader,name,value),(c->shader,c->name,c->value))
SYNC_VOID(glGetShaderInfoLog,(GLuint shader,GLsizei size,GLsizei *length,GLchar *log),(GLuint shader; GLsizei size; GLsizei *length; GLchar *log;),(shader,size,length,log),(c->shader,c->size,c->length,c->log))
SYNC_VOID(glAttachShader,(GLuint program,GLuint shader),(GLuint program,shader;),(program,shader),(c->program,c->shader))
SYNC_VOID(glBindAttribLocation,(GLuint program,GLuint index,const GLchar *name),(GLuint program,index; const GLchar *name;),(program,index,name),(c->program,c->index,c->name))
SYNC_VOID(glLinkProgram,(GLuint program),(GLuint program;),(program),(c->program))
SYNC_VOID(glProgramBinary,(GLuint program,GLenum format,const void *binary,GLsizei bytes),(GLuint program; GLenum format; const void *binary; GLsizei bytes;),(program,format,binary,bytes),(c->program,c->format,c->binary,c->bytes))
SYNC_VOID(glGetProgramBinary,(GLuint program,GLsizei size,GLsizei *bytes,GLenum *format,void *binary),(GLuint program; GLsizei size; GLsizei *bytes; GLenum *format; void *binary;),(program,size,bytes,format,binary),(c->program,c->size,c->bytes,c->format,c->binary))
ASYNC(glProgramParameteri,(GLuint program,GLenum name,GLint value),(GLuint program; GLenum name; GLint value;),(program,name,value),(c->program,c->name,c->value))
SYNC_VOID(glGetProgramiv,(GLuint program,GLenum name,GLint *value),(GLuint program; GLenum name; GLint *value;),(program,name,value),(c->program,c->name,c->value))
SYNC_VOID(glGetProgramInfoLog,(GLuint program,GLsizei size,GLsizei *length,GLchar *log),(GLuint program; GLsizei size; GLsizei *length; GLchar *log;),(program,size,length,log),(c->program,c->size,c->length,c->log))
SYNC_VOID(glDeleteShader,(GLuint shader),(GLuint shader;),(shader),(c->shader))
SYNC_RESULT(GLint,glGetUniformLocation,(GLuint program,const GLchar *name),(GLuint program; const GLchar *name;),(program,name),(c->program,c->name))
SYNC_VOID(glCompressedTexImage2D,(GLenum target,GLint level,GLenum format,GLsizei w,GLsizei h,GLint border,GLsizei size,const void *pixels),(GLenum target; GLint level; GLenum format; GLsizei w,h; GLint border; GLsizei size; const void *pixels;),(target,level,format,w,h,border,size,pixels),(c->target,c->level,c->format,c->w,c->h,c->border,c->size,c->pixels))
SYNC_VOID(glGenFramebuffers,(GLsizei n,GLuint *names),(GLsizei n; GLuint *names;),(n,names),(c->n,c->names))
SYNC_RESULT(GLenum,glCheckFramebufferStatus,(GLenum target),(GLenum target;),(target),(c->target))
SYNC_VOID(glDeleteFramebuffers,(GLsizei n,const GLuint *names),(GLsizei n; const GLuint *names;),(n,names),(c->n,c->names))
SYNC_VOID(glGenSamplers,(GLsizei n,GLuint *names),(GLsizei n; GLuint *names;),(n,names),(c->n,c->names))

/* Resource owners may disappear immediately after release. Keep names in the
 * ordered command, so preceding draws finish using them before driver deletion. */
#define DELETE_NAMES(name) \
    typedef struct { GLsizei n; const GLuint *names; } Args_##name; \
    static void run_##name(const void *data) { \
        const Args_##name *c = data; driver_##name(c->n,c->names); \
    } \
    static void queued_##name(GLsizei n,const GLuint *names) { \
        size_t bytes = names && n > 0 ? (size_t)n * sizeof *names : 0; \
        Args_##name *c = record(run_##name,sizeof *c + bytes); \
        *c = (Args_##name){n,names}; \
        if (bytes) { memcpy(c+1,names,bytes); c->names = (const GLuint *)(c+1); } \
    }
DELETE_NAMES(glDeleteTextures)
DELETE_NAMES(glDeleteBuffers)

typedef struct SamplerValues { GLuint sampler; GLenum name; const GLfloat *values; } SamplerValues;
static void run_glSamplerParameterfv(const void *data) {
    const SamplerValues *c = data;
    driver_glSamplerParameterfv(c->sampler,c->name,c->values);
}
static void queued_glSamplerParameterfv(GLuint sampler,GLenum name,const GLfloat *values) {
    size_t bytes = values ? (name == GL_TEXTURE_BORDER_COLOR ? 4 : 1) * sizeof *values : 0;
    SamplerValues *c = record(run_glSamplerParameterfv,sizeof *c + bytes);
    *c = (SamplerValues){sampler,name,values};
    if (bytes) { memcpy(c+1,values,bytes); c->values = (const GLfloat *)(c+1); }
}

typedef struct PixelStore { GLenum name; GLint value; } PixelStore;
static void run_glPixelStorei(const void *data) {
    const PixelStore *c = data; driver_glPixelStorei(c->name,c->value);
}
static void queued_glPixelStorei(GLenum name,GLint value) {
    if (name == GL_UNPACK_ALIGNMENT && (value == 1 || value == 2 || value == 4 || value == 8))
        unpack_alignment = value;
    if (value >= 0) {
        if (name == GL_UNPACK_ROW_LENGTH) unpack_row_length = value;
        if (name == GL_UNPACK_SKIP_ROWS) unpack_skip_rows = value;
        if (name == GL_UNPACK_SKIP_PIXELS) unpack_skip_pixels = value;
    }
    *(PixelStore *)record(run_glPixelStorei,sizeof(PixelStore)) = (PixelStore){name,value};
}
typedef struct BindBuffer { GLenum target; GLuint buffer; } BindBuffer;
static void run_glBindBuffer(const void *data) {
    const BindBuffer *c = data; driver_glBindBuffer(c->target,c->buffer);
}
static void queued_glBindBuffer(GLenum target,GLuint buffer) {
    if (target == GL_PIXEL_UNPACK_BUFFER) unpack_buffer = (GLint)buffer;
    *(BindBuffer *)record(run_glBindBuffer,sizeof(BindBuffer)) = (BindBuffer){target,buffer};
}

/* Copy exactly through last pixel; row padding/skip state remains ordered.
 * Unknown formats and buffer offsets keep original synchronous semantics. */
static int pixel_bytes(GLsizei w,GLsizei h,GLenum format,GLenum type,size_t *bytes) {
    if (unpack_buffer || w < 0 || h < 0) return 0;
    size_t bpp = 0;
    if (type == GL_UNSIGNED_BYTE || type == GL_BYTE) {
        switch (format) {
        case GL_RED: bpp = 1; break;
        case GL_RG: bpp = 2; break;
        case GL_RGB: bpp = 3; break;
        case GL_RGBA: case GL_BGRA: bpp = 4; break;
        }
    } else if (type == GL_UNSIGNED_SHORT_5_6_5 && format == GL_RGB) bpp = 2;
    else if ((type == GL_UNSIGNED_SHORT_1_5_5_5_REV || type == GL_UNSIGNED_SHORT_4_4_4_4_REV) &&
             (format == GL_RGBA || format == GL_BGRA)) bpp = 2;
    if (!bpp) return 0;
    if (!w || !h) { *bytes = 0; return 1; }
    size_t stride = (unpack_row_length ? (size_t)unpack_row_length : (size_t)w) * bpp;
    stride = (stride + unpack_alignment - 1) & ~(size_t)(unpack_alignment - 1);
    size_t rows = (size_t)unpack_skip_rows + h - 1;
    size_t last = ((size_t)unpack_skip_pixels + w) * bpp;
    if (stride && rows > (SIZE_MAX - last) / stride) return 0;
    *bytes = rows * stride + last;
    return 1;
}
typedef struct Image { GLenum target; GLint level,x,y; GLsizei w,h; GLenum format,type; const void *pixels; } Image;
static void run_glTexSubImage2D(const void *data) {
    const Image *c = data;
    driver_glTexSubImage2D(c->target,c->level,c->x,c->y,c->w,c->h,c->format,c->type,c->pixels);
}
static void sync_image(void *data) { run_glTexSubImage2D(data); }
static void queued_glTexSubImage2D(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,
                                 GLenum format,GLenum type,const void *pixels) {
    Image image = {target,level,x,y,w,h,format,type,pixels};
    size_t bytes;
    if (!pixel_bytes(w,h,format,type,&bytes)) {
        synchronize(sync_image,&image,&cost_glTexSubImage2D); return;
    }
    if (!pixels) bytes = 0;
    Image *c = record(run_glTexSubImage2D,sizeof *c + bytes);
    *c = image;
    if (bytes) { memcpy(c+1,pixels,bytes); c->pixels = c+1; }
}
typedef struct CompressedImage { GLenum target; GLint level,x,y; GLsizei w,h; GLenum format; GLsizei size; const void *pixels; } CompressedImage;
static void run_glCompressedTexSubImage2D(const void *data) {
    const CompressedImage *c = data;
    driver_glCompressedTexSubImage2D(c->target,c->level,c->x,c->y,c->w,c->h,c->format,c->size,c->pixels);
}
static void sync_compressed_image(void *data) { run_glCompressedTexSubImage2D(data); }
static void queued_glCompressedTexSubImage2D(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,
                                           GLenum format,GLsizei size,const void *pixels) {
    CompressedImage image = {target,level,x,y,w,h,format,size,pixels};
    if (unpack_buffer || size < 0) {
        synchronize(sync_compressed_image,&image,&cost_glCompressedTexSubImage2D); return;
    }
    size_t bytes = pixels ? (size_t)size : 0;
    CompressedImage *c = record(run_glCompressedTexSubImage2D,sizeof *c + bytes);
    *c = image;
    if (bytes) { memcpy(c+1,pixels,bytes); c->pixels = c+1; }
}

static void run_glGetError(void *data) { *(GLenum *)data = driver_glGetError(); }
static GLenum queued_glGetError(void) { GLenum result; synchronize(run_glGetError, &result, &cost_glGetError); return result; }
static void run_glCreateProgram(void *data) { *(GLuint *)data = driver_glCreateProgram(); }
static GLuint queued_glCreateProgram(void) { GLuint result; synchronize(run_glCreateProgram, &result, &cost_glCreateProgram); return result; }

typedef struct BufferData { GLenum target, usage; GLsizeiptr size; const void *data; } BufferData;
static void run_glBufferData(const void *data) {
    const BufferData *c = data; driver_glBufferData(c->target,c->size,c->data,c->usage);
}
static void queued_glBufferData(GLenum target,GLsizeiptr size,const void *data,GLenum usage) {
    size_t bytes = data && size > 0 ? (size_t)size : 0;
    BufferData *c = record(run_glBufferData, sizeof *c + bytes);
    *c = (BufferData){target,usage,size,data};
    if (bytes) { memcpy(c+1,data,bytes); c->data = c+1; }
}
typedef struct BufferSubData { GLenum target; GLintptr offset; GLsizeiptr size; const void *data; } BufferSubData;
static void run_glBufferSubData(const void *data) {
    const BufferSubData *c = data; driver_glBufferSubData(c->target,c->offset,c->size,c->data);
}
static void queued_glBufferSubData(GLenum target,GLintptr offset,GLsizeiptr size,const void *data) {
    size_t bytes = data && size > 0 ? (size_t)size : 0;
    BufferSubData *c = record(run_glBufferSubData, sizeof *c + bytes);
    *c = (BufferSubData){target,offset,size,data};
    if (bytes) { memcpy(c+1,data,bytes); c->data = c+1; }
}

#define UNIFORM(name, type, components) \
    typedef struct { GLint location; GLsizei count; const type *values; } Args_##name; \
    static void run_##name(const void *data) { \
        const Args_##name *c = data; driver_##name(c->location,c->count,c->values); \
    } \
    static void queued_##name(GLint location,GLsizei count,const type *values) { \
        size_t bytes = values && count > 0 ? (size_t)count * components * sizeof(type) : 0; \
        Args_##name *c = record(run_##name, sizeof *c + bytes); \
        *c = (Args_##name){location,count,values}; \
        if (bytes) { memcpy(c+1,values,bytes); c->values = (const type *)(c+1); } \
    }
UNIFORM(glUniform4fv,GLfloat,4)
UNIFORM(glUniform1iv,GLint,1)
#define MATRIX(name, components) \
    typedef struct { GLint location; GLsizei count; GLboolean transpose; const GLfloat *values; } Args_##name; \
    static void run_##name(const void *data) { \
        const Args_##name *c = data; driver_##name(c->location,c->count,c->transpose,c->values); \
    } \
    static void queued_##name(GLint location,GLsizei count,GLboolean transpose,const GLfloat *values) { \
        size_t bytes = values && count > 0 ? (size_t)count * components * sizeof(GLfloat) : 0; \
        Args_##name *c = record(run_##name, sizeof *c + bytes); \
        *c = (Args_##name){location,count,transpose,values}; \
        if (bytes) { memcpy(c+1,values,bytes); c->values = (const GLfloat *)(c+1); } \
    }
MATRIX(glUniformMatrix4fv,16)
MATRIX(glUniformMatrix3fv,9)

typedef struct Swap { SDL_Window *window; ProfileSwap profile; } Swap;
static uint64_t frame_period, frame_frequency, frame_deadline;
static int frame_pacing_initialized;
static void pace_frame(uint64_t start) {
    if (!frame_pacing_initialized) {
        const char *limit = getenv("SH3_FPS_LIMIT");
        frame_frequency = SDL_GetPerformanceFrequency();
        frame_period = limit && !strcmp(limit,"30") ? frame_frequency / 30 : 0;
        frame_pacing_initialized = 1;
        if (frame_period) puts("frame_limit=30");
    }
    if (!frame_period) return;
    /* Stable phase includes render work and scheduler jitter. Discard debt once
     * more than one period late instead of trying to repay a loading stall. */
    if (!frame_deadline || start > frame_deadline + frame_period)
        frame_deadline = start;
    frame_deadline += frame_period;
    uint64_t now = SDL_GetPerformanceCounter();
    if (now < frame_deadline) {
        uint64_t ms = ((frame_deadline - now) * 1000 + frame_frequency - 1) / frame_frequency;
        SDL_Delay((Uint32)ms);
    }
}
static uint64_t swap_now(const Swap *swap) {
    profile_gpu_end(swap->profile);
    uint64_t start = SDL_GetPerformanceCounter();
    SDL_GL_SwapWindow(swap->window);
    profile_swap_end(swap->profile, swap->profile.enabled ? start : 0);
    return start;
}
static void run_swap(const void *data) {
    uint64_t start = swap_now(data);
    SDL_LockMutex(mutex);
    /* Bound producer against actual swap completion, allowing its next CPU
     * frame to overlap intentional worker sleep without adding queued frames. */
    completed_frames++;
    SDL_CondBroadcast(condition);
    SDL_UnlockMutex(mutex);
    pace_frame(start);
}
void gl_swap_window(SDL_Window *window) {
    Swap swap = {window, profile_swap_snapshot()};
    if (!active) { pace_frame(swap_now(&swap)); return; }
    *(Swap *)record(run_swap,sizeof swap) = swap;
    submitted_frames++;
    publish();
    SDL_LockMutex(mutex);
    while (completed_frames + 1 < submitted_frames) SDL_CondWait(condition,mutex);
    SDL_UnlockMutex(mutex);
}

int gl_thread_start(void) {
    if (active) return 1;
    const char *enabled = getenv("SH3_GL_THREAD");
    if (enabled && !strcmp(enabled,"0")) return 0;
    queue_stats = getenv("SH3_PROFILE") != NULL || getenv("SH3_GL_QUEUE_STATS") != NULL;
    context = SDL_GL_GetCurrentContext();
    p_glGetIntegerv(GL_UNPACK_ALIGNMENT,&unpack_alignment);
    p_glGetIntegerv(GL_UNPACK_ROW_LENGTH,&unpack_row_length);
    p_glGetIntegerv(GL_UNPACK_SKIP_ROWS,&unpack_skip_rows);
    p_glGetIntegerv(GL_UNPACK_SKIP_PIXELS,&unpack_skip_pixels);
    p_glGetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING,&unpack_buffer);
    producer = SDL_ThreadID();
    mutex = SDL_CreateMutex(); condition = SDL_CreateCond();
    if (!context || !mutex || !condition) rt_fatal("GL worker setup failed: %s",SDL_GetError());
    if (SDL_GL_MakeCurrent(rt_window,NULL)) rt_fatal("GL context detach failed: %s",SDL_GetError());
    worker = SDL_CreateThread(render_worker,"sh3-gl",NULL);
    if (!worker) rt_fatal("GL worker creation failed: %s",SDL_GetError());
    SDL_LockMutex(mutex);
    while (!started) SDL_CondWait(condition,mutex);
    SDL_UnlockMutex(mutex);
    if (start_failed) rt_fatal("GL worker context transfer failed");
#define INSTALL(type, name) driver_##name = p_##name; if (p_##name) p_##name = queued_##name;
    GL_FUNCS(INSTALL)
#undef INSTALL
    active = 1;
    atexit(gl_thread_stop);
    puts("gl_thread=enabled max_frames_ahead=1");
    return 1;
}

void gl_thread_stop(void) {
    if (!active) return;
    if (SDL_ThreadID() != producer) return;
    wait_job(publish());
    SDL_LockMutex(mutex); stopping = 1; SDL_CondBroadcast(condition); SDL_UnlockMutex(mutex);
    int status;
    SDL_WaitThread(worker,&status);
    int restored = !SDL_GL_MakeCurrent(rt_window,context);
#define RESTORE(type, name) p_##name = driver_##name;
    GL_FUNCS(RESTORE)
#undef RESTORE
    active = 0;
    for (unsigned i=0;i<3;i++) { free(chunks[i].data); memset(&chunks[i],0,sizeof chunks[i]); }
    SDL_DestroyCond(condition); SDL_DestroyMutex(mutex);
    if (queue_stats) {
        double milliseconds = 1000.0 / SDL_GetPerformanceFrequency();
#define REPORT_COST(type, name) \
        if (cost_##name.calls) printf("gl_queue_sync name=%s calls=%llu wait_ms=%.3f\n", \
            cost_##name.api, (unsigned long long)cost_##name.calls, cost_##name.ticks * milliseconds); \
        cost_##name.calls = cost_##name.ticks = 0;
        GL_FUNCS(REPORT_COST)
#undef REPORT_COST
    }
    queue_stats = 0;
    condition = NULL; mutex = NULL; worker = NULL; building = NULL;
    write_slot = read_slot = 0;
    submitted_jobs = completed_jobs = submitted_frames = completed_frames = 0;
    stopping = started = start_failed = 0;
    frame_period = frame_frequency = frame_deadline = 0;
    frame_pacing_initialized = 0;
    printf("gl_thread=stopped restored=%s\n",restored && !status ? "yes" : "no");
    if (!restored || status) rt_fatal("GL context restore failed");
}
