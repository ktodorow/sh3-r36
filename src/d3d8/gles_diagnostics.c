/* Installed-launcher diagnostics. Never infer hardware support from host fixtures. */
#ifndef __SWITCH__
#include "d3d8.h"
#ifdef SH3_GLES_SAMPLES
#include "shader_samples.h"
#endif

static uint32_t copy_guest(const void *data, size_t size) {
    uint32_t va = galloc(size);
    memcpy(GPTR(va), data, size);
    return va;
}

static uint32_t method(uint32_t object, int slot, int count, const uint32_t *arguments) {
    uint32_t args[12] = {object};
    memcpy(args + 1, arguments, count * 4);
    return guest_call(MEM32(MEM32(object) + slot * 4), count + 1, args, 1);
}
#define DEVICE(slot, ...) method(dev->obj, slot, sizeof((uint32_t[]){__VA_ARGS__}) / 4, (uint32_t[]){__VA_ARGS__})

static unsigned char frame[64 * 48 * 4];
static int capture(const char *name) {
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(0, 0, 64, 48, GL_RGBA, GL_UNSIGNED_BYTE, frame);
    FILE *file = fopen(name, "wb");
    if (!file) return 0;
    fprintf(file, "P6\n64 48\n255\n");
    for (int i = 0; i < 64 * 48; i++) fwrite(frame + i * 4, 1, 3, file);
    int ok = !ferror(file);
    fclose(file);
    return ok;
}

static int pixel(int x, int y, int r, int g, int b) {
    unsigned char *p = frame + (y * 64 + x) * 4;
    if (p[0] == r && p[1] == g && p[2] == b) return 1;
    printf("pixel_mismatch=%d,%d expected=%d,%d,%d actual=%u,%u,%u\n", x, y, r, g, b, p[0], p[1], p[2]);
    return 0;
}

static int indexed_sample(void) {
#ifndef SH3_GLES_SAMPLES
    puts("sample=UNAVAILABLE rebuild with owner-derived samples");
    return 0;
#else
    extern const Bridge __start_game_bridges[], __stop_game_bridges[];
    uint32_t d3d = 0;
    for (const Bridge *b = __start_game_bridges; b < __stop_game_bridges; b++)
        if (!strcmp(b->name, "Direct3DCreate8")) {
            uint32_t arg = 220;
            d3d = guest_call(rt_host_fn(b->name, b->fn), 1, &arg, 1);
        }
    if (!d3d) return 0;
    uint32_t pp = galloc(56), result = galloc(4);
    MEM32(pp) = 64; MEM32(pp + 4) = 48; MEM32(pp + 8) = FMT_A8R8G8B8;
    MEM32(pp + 28) = 1; MEM32(pp + 32) = 1; MEM32(pp + 36) = FMT_D24S8;
    if (method(d3d, 15, 6, (uint32_t[]){0, 1, 0, 2, pp, result})) return 0;
    printf("sample_input_sha1=%s\nsample_vs_offset=%08x\nsample_ps_offset=%08x\nsample_decl_va=%08x\n",
           SAMPLE_INPUT_SHA1, SAMPLE_VS_OFFSET, SAMPLE_PS_OFFSET, SAMPLE_DECL_VA);
    dev->vs = shader_create_vs(copy_guest(sample_decl, sizeof sample_decl), copy_guest(sample_vs, sizeof sample_vs));
    dev->ps = shader_create_ps(copy_guest(sample_ps, sizeof sample_ps));
    for (int i = 0; i < 4; i++) { dev->vsc[2 + i][i] = 1; dev->vsc[0][i] = 1; }
    /* Analytic indexed quad using game's exact position/normal/UV declaration.
     * Prefix vertices and index prefix poison an ignored base or index offset. */
    const float vertices[][8] = {
        {8,8,8}, {8,8,8}, {8,8,8},
        {-.75f,.75f,.5f, 0,0,1, 0,0}, {.75f,.75f,.5f, 0,0,1, 1,0},
        {-.75f,-.75f,.5f, 0,0,1, 0,1}, {.75f,-.75f,.5f, 0,0,1, 1,1},
    };
    const uint16_t indices[] = {0,0, 0,1,2, 2,1,3};
    dev->stream[0] = res_buffer(RES_VB, sizeof vertices, 0, 0, 0);
    Res *vb = res_of(dev->stream[0]); memcpy(GPTR(vb->mem), vertices, sizeof vertices); vb->dirty = 1;
    dev->stride[0] = sizeof vertices[0];
    dev->ib = res_buffer(RES_IB, sizeof indices, 0, FMT_INDEX16, 0);
    Res *ib = res_of(dev->ib); memcpy(GPTR(ib->mem), indices, sizeof indices); ib->dirty = 1;
    dev->base_vertex = 3;
    dev->tex[0] = res_texture(2, 2, 1, 0, FMT_P8, 0, 0);
    Res *texture = res_of(dev->tex[0]), *level = res_of(texture->surf[0][0]);
    memcpy(GPTR(level->mem), (uint8_t[]){1,2,3,4}, 4); texture->dirty = level->dirty = 1;
    dev->palette[0] = calloc(256, 4);
    memcpy(dev->palette[0] + 1, (uint32_t[]){0xff0000ff,0xff00ff00,0xffff0000,0xff00ffff}, 16);
    glClearColor(0, 0, 0, 1); glClearDepth(1); glClearStencil(0);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT);
    if (DEVICE(71, 4, 0, 4, 2, 2)) return 0;
    int ok = capture("indexed.ppm");
    ok &= pixel(16,12,255,0,0) & pixel(48,12,0,255,0) & pixel(16,36,0,0,255) & pixel(48,36,255,255,0);
    ok &= pixel(2,2,0,0,0) & pixel(62,46,0,0,0);
    GLenum error = glGetError();
    printf("indexed_gl_error=%04x\nindexed_base_vertex=%s\n", error, ok && !error ? "PASS" : "FAIL");
    ok &= !error;
    printf("sample_geometry_va=%08x\n", SAMPLE_GEOMETRY_VA);
    dev->vs = 0x104; /* Original game's XYZRHW + UV FVF. */
    dev->rs[22] = 1;
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT);
    if (DEVICE(72, 5, 2, copy_guest(sample_geometry, sizeof sample_geometry), 24)) return 0;
    int quad = capture("game-quad.ppm");
    quad &= pixel(16,12,255,0,0) & pixel(48,12,0,255,0);
    quad &= pixel(16,40,0,0,255) & pixel(48,40,255,255,0);
    error = glGetError();
    printf("game_quad_gl_error=%04x\ngame_quad=%s\n", error, quad && !error ? "PASS" : "FAIL");
    ok &= quad && !error;
    printf("sample_skin_offset=%08x\nsample_color_offset=%08x\n", SAMPLE_SKIN_OFFSET, SAMPLE_COLOR_OFFSET);
    dev->vs = shader_create_vs(copy_guest(sample_skin_decl, sizeof sample_skin_decl), copy_guest(sample_skin, sizeof sample_skin));
    dev->ps = shader_create_ps(copy_guest(sample_color, sizeof sample_color));
    dev->vsc[0][3] = 255;
    for (int bone = 0; bone < 4; bone++)
        for (int row = 0; row < 3; row++) dev->vsc[48 + bone * 3 + row][row] = bone + 1;
    struct SkinVertex { float p[3], weights[3]; uint32_t bones; float n[3], uv[2]; };
    const struct SkinVertex skin[] = {
        {{-.25f,.25f,.125f}, {.125f,.25f,.375f},0x09060300,{0,0,1},{0,0}},
        {{.25f,.25f,.125f}, {.125f,.25f,.375f},0x09060300,{0,0,1},{1,0}},
        {{-.25f,-.25f,.125f}, {.125f,.25f,.375f},0x09060300,{0,0,1},{0,1}},
        {{.25f,-.25f,.125f}, {.125f,.25f,.375f},0x09060300,{0,0,1},{1,1}},
    };
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT);
    if (DEVICE(72, 5, 2, copy_guest(skin, sizeof skin), sizeof skin[0])) return 0;
    int skinned = capture("skinning.ppm");
    skinned &= pixel(12,12,255,0,0) & pixel(52,12,0,255,0);
    skinned &= pixel(12,36,0,0,255) & pixel(52,36,255,255,0) & pixel(2,2,0,0,0);
    error = glGetError();
    printf("skinning_gl_error=%04x\nskinning=%s\n", error, skinned && !error ? "PASS" : "FAIL");
    return ok && skinned && !error;
#endif
}

static int scissor_sample(void) {
    if (!dev) return 0;
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    const int32_t rect[] = {4, 5, 20, 18};
    DEVICE(36, 1, copy_guest(rect, sizeof rect), 1, 0xffff0000, 0, 0);
    int ok = capture("scissor.ppm");
    ok &= pixel(8,8,255,0,0) & pixel(8,40,0,0,0) & pixel(24,8,0,0,0);
    GLenum error = glGetError();
    printf("scissor_gl_error=%04x\nclear_scissor=%s\n", error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
}

static void solid_quad(float z, uint32_t rgba, int reverse) {
    float vertices[][8] = {
        {-.75f,.75f,z,0,0,1,0,0}, {.75f,.75f,z,0,0,1,0,0},
        {-.75f,-.75f,z,0,0,1,0,0}, {.75f,-.75f,z,0,0,1,0,0},
    };
    if (reverse) for (int i = 0; i < 4; i += 2) {
        float swap[8]; memcpy(swap, vertices[i], sizeof swap);
        memcpy(vertices[i], vertices[i + 1], sizeof swap); memcpy(vertices[i + 1], swap, sizeof swap);
    }
    dev->palette[0][1] = rgba;
    Res *texture = res_of(dev->tex[0]);
    texture->dirty = res_of(texture->surf[0][0])->dirty = 1;
    DEVICE(72, 5, 2, copy_guest(vertices, sizeof vertices), sizeof vertices[0]);
}

static int culling_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    if (!dev) return 0;
    dev->vs = shader_create_vs(copy_guest(sample_decl, sizeof sample_decl), copy_guest(sample_vs, sizeof sample_vs));
    dev->ps = shader_create_ps(copy_guest(sample_ps, sizeof sample_ps));
    dev->vsc[0][3] = 1;
    const char *name[] = {"cw-keep.ppm", "cw-drop.ppm", "ccw-drop.ppm", "ccw-keep.ppm"};
    int ok = 1;
    for (int i = 0; i < 4; i++) {
        DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
        dev->rs[22] = i & 1 ? 2 : 3;
        solid_quad(.5f, 0xff0000ff, i >= 2);
        ok &= capture(name[i]);
        ok &= pixel(32,24,i == 0 || i == 3 ? 255 : 0,0,0);
    }
    dev->rs[22] = 1;
    GLenum error = glGetError();
    printf("culling_gl_error=%04x\nculling=%s\n", error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
#endif
}

static int depth_sample(void) {
    if (!dev) return 0;
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    dev->rs[7] = 0;
    solid_quad(-.25f, 0xff0000ff, 0);
    solid_quad(1.25f, 0xffff0000, 0);
    int ok = capture("depth-clip.ppm");
    ok &= pixel(32,24,0,0,0);
    dev->rs[7] = dev->rs[14] = 1; dev->rs[23] = 2; /* LESS */
    solid_quad(.75f, 0xff0000ff, 0);
    solid_quad(.25f, 0xff00ff00, 0);
    solid_quad(.5f, 0xffff0000, 0);
    ok &= capture("depth-order.ppm");
    ok &= pixel(32,24,0,255,0);
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    dev->rs[14] = 0;
    solid_quad(.25f, 0xff0000ff, 0);
    dev->rs[14] = 1;
    solid_quad(.75f, 0xffff0000, 0);
    ok &= capture("depth-write.ppm");
    ok &= pixel(32,24,0,0,255);
    GLenum error = glGetError();
    printf("depth_gl_error=%04x\ndepth=%s\n", error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
}

static int stencil_sample(void) {
    if (!dev) return 0;
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    dev->rs[7] = 0; dev->rs[52] = 1;
    dev->rs[53] = dev->rs[54] = 1; dev->rs[55] = 3; /* KEEP, KEEP, REPLACE */
    dev->rs[56] = 8; dev->rs[57] = 3; dev->rs[58] = dev->rs[59] = 255;
    dev->rs[168] = 0;
    solid_quad(.5f, 0xff0000ff, 0); /* Write stencil 3 without color. */
    dev->rs[59] = 0; dev->rs[57] = 5;
    solid_quad(.5f, 0xff0000ff, 0); /* Mask must prevent replacing 3 with 5. */
    dev->rs[168] = 15; dev->rs[56] = 3; dev->rs[57] = 3; dev->rs[55] = 1;
    solid_quad(.5f, 0xff00ff00, 0);
    dev->rs[57] = 4;
    solid_quad(.5f, 0xff0000ff, 0); /* EQUAL must reject. */
    int ok = capture("stencil-mask.ppm");
    ok &= pixel(32,24,0,255,0) & pixel(2,2,0,0,0);
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    dev->rs[52] = 0; dev->rs[7] = 1;
    solid_quad(.25f, 0xffff0000, 0);
    dev->rs[52] = 1; dev->rs[56] = 8; dev->rs[57] = 1; dev->rs[59] = 255;
    dev->rs[54] = 3; dev->rs[168] = 0;
    solid_quad(.75f, 0xff0000ff, 0); /* Depth fail replaces stencil with 1. */
    dev->rs[7] = 0; dev->rs[56] = 3; dev->rs[59] = 0; dev->rs[168] = 15;
    solid_quad(.5f, 0xff00ff00, 0);
    ok &= capture("stencil-zfail.ppm");
    ok &= pixel(32,24,0,255,0) & pixel(2,2,0,0,0);
    dev->rs[52] = 0; dev->rs[54] = 1;
    GLenum error = glGetError();
    printf("stencil_gl_error=%04x\nstencil=%s\n", error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
}

static int precision_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    if (!dev) return 0;
    glDisable(GL_DITHER);
    dev->rs[7] = 0;
    dev->vsc[2][3] = -4096;
    const float vertices[][8] = {
        {4096-.75f,.75f,.5f,0,0,1,0,0}, {4096+.75f,.75f,.5f,0,0,1,0,0},
        {4096-.75f,-.75f,.5f,0,0,1,0,0}, {4096+.75f,-.75f,.5f,0,0,1,0,0},
    };
    dev->palette[0][1] = 0xffffffff;
    Res *texture = res_of(dev->tex[0]);
    texture->dirty = res_of(texture->surf[0][0])->dirty = 1;
    uint32_t data = copy_guest(vertices, sizeof vertices);
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    DEVICE(72, 5, 2, data, sizeof vertices[0]);
    int ok = capture("precision-vertex.ppm");
    ok &= pixel(16,12,255,255,255) & pixel(48,36,255,255,255) & pixel(2,2,0,0,0);
    dev->ps = shader_create_ps(copy_guest(sample_precision, sizeof sample_precision));
    for (int i = 0; i < 4; i++) {
        dev->psc[0][i] = 4095.f / 4096.f; dev->psc[1][i] = -.5f; dev->psc[2][i] = .25f;
    }
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    DEVICE(72, 5, 2, data, sizeof vertices[0]);
    ok &= capture("precision-fragment.ppm");
    ok &= pixel(16,12,127,127,127) & pixel(48,36,127,127,127);
    dev->vsc[2][3] = 0;
    GLenum error = glGetError();
    printf("sample_precision_offset=%08x\nprecision_gl_error=%04x\nprecision_render=%s\n",
           SAMPLE_PRECISION_OFFSET, error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
#endif
}

static int rhw_depth_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    if (!dev) return 0;
    dev->ps = shader_create_ps(copy_guest(sample_ps, sizeof sample_ps));
    dev->vs = 0x104;
    dev->rs[7] = dev->rs[14] = 1; dev->rs[23] = 2;
    const float vertices[][6] = {
        {8,8,-.5f,.5f,0,0}, {56,8,-.5f,.5f,0,0},
        {8,40,1.5f,2,0,0}, {56,40,1.5f,2,0,0},
    };
    dev->palette[0][1] = 0xff00ff00;
    Res *texture = res_of(dev->tex[0]);
    texture->dirty = res_of(texture->surf[0][0])->dirty = 1;
    /* At y=16 original linear screen depth is 0; clamping vertices first gives .25.
     * Varying reciprocal W also detects a perspective-interpolated depth mistake. */
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3e000000, 0); /* Clear depth .125. */
    DEVICE(72, 5, 2, copy_guest(vertices, sizeof vertices), sizeof vertices[0]);
    int ok = capture("rhw-depth.ppm");
    ok &= pixel(32,16,0,255,0) & pixel(32,24,0,0,0) & pixel(2,2,0,0,0);
    GLenum error = glGetError();
    printf("rhw_depth_gl_error=%04x\nrhw_depth=%s\n", error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
#endif
}

static int packed_color_sample(void) {
    if (!dev) return 0;
    struct ColorVertex { float p[4]; uint32_t color; float uv[2]; };
    const struct ColorVertex vertices[] = {
        {{8,8,.5f,1},0xffe02080,{0,0}}, {{56,8,.5f,1},0xffe02080,{0,0}},
        {{8,40,.5f,1},0xffe02080,{0,0}}, {{56,40,.5f,1},0xffe02080,{0,0}},
    };
    dev->vs = 0x144; dev->ps = 0; dev->rs[7] = 0;
    dev->palette[0][1] = 0xffffffff;
    Res *texture = res_of(dev->tex[0]);
    texture->dirty = res_of(texture->surf[0][0])->dirty = 1;
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    DEVICE(72, 5, 2, copy_guest(vertices, sizeof vertices), sizeof vertices[0]);
    int ok = capture("packed-color.ppm");
    ok &= pixel(32,24,224,32,128) & pixel(2,2,0,0,0);
    GLenum error = glGetError();
    printf("packed_color_gl_error=%04x\npacked_color=%s\n", error, ok && !error ? "PASS" : "FAIL");
    return ok && !error;
}

static int presentation_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    if (!dev) return 0;
    dev->vs = 0x104;
    dev->ps = shader_create_ps(copy_guest(sample_ps, sizeof sample_ps));
    dev->rs[7] = 0;
    memcpy(dev->palette[0] + 1, (uint32_t[]){0xff0000ff,0xff00ff00,0xffff0000,0xff00ffff}, 16);
    Res *texture = res_of(dev->tex[0]);
    texture->dirty = res_of(texture->surf[0][0])->dirty = 1;
    DEVICE(36, 0, 0, 7, 0xff000000, 0x3f800000, 0);
    DEVICE(72, 5, 2, copy_guest(sample_geometry, sizeof sample_geometry), 24);
    setenv("SH3_PRESENT_DUMP", "present.ppm", 1);
    int ok = !DEVICE(15, 0, 0, 0, 0);
    unsetenv("SH3_PRESENT_DUMP");
    int w = 0, h = 0;
    FILE *file = fopen("present.ppm", "rb");
    char line[64];
    if (!file) return 0;
    ok &= fgets(line, sizeof line, file) && !strcmp(line, "P6\n");
    ok &= fgets(line, sizeof line, file) && sscanf(line, "%d %d", &w, &h) == 2;
    ok &= fgets(line, sizeof line, file) && !strcmp(line, "255\n");
    if (w < 4 || h < 6 || w > 8192 || h > 8192) { fclose(file); return 0; }
    size_t size = (size_t)w * h * 3;
    uint8_t *pixels = malloc(size);
    if (!pixels) { fclose(file); return 0; }
    ok &= fread(pixels, 1, size, file) == size;
    fclose(file);
    const uint8_t expected[][3] = {{255,0,0}, {0,255,0}, {0,0,255}, {255,255,0}};
    for (int i = 0; i < 4; i++) {
        int x = i & 1 ? 3 * w / 4 : w / 4, y = i < 2 ? h / 4 : 5 * h / 6;
        ok &= !memcmp(pixels + ((size_t)y * w + x) * 3, expected[i], 3);
    }
    free(pixels);
    GLenum error = glGetError();
    printf("presentation_size=%d,%d\npresentation_gl_error=%04x\npresentation=%s\n", w, h, error, ok && !error ? "PASS" : "FAIL");
    SDL_Delay(3000);
    return ok && !error;
#endif
}

static int desktop_reference(void) {
    const char *value = getenv("SH3_GRAPHICS_REFERENCE");
    return value && !strcmp(value, "1");
}

static int identity(void) {
    p_glGetString = (void *)SDL_GL_GetProcAddress("glGetString");
    p_glGetStringi = (void *)SDL_GL_GetProcAddress("glGetStringi");
    p_glGetIntegerv = (void *)SDL_GL_GetProcAddress("glGetIntegerv");
    void (*precision)(GLenum, GLenum, GLint *, GLint *) = SDL_GL_GetProcAddress("glGetShaderPrecisionFormat");
    if (!p_glGetString || !p_glGetStringi || !p_glGetIntegerv || !precision) return 0;
    const char *vendor = (const char *)glGetString(GL_VENDOR);
    const char *renderer = (const char *)glGetString(GL_RENDERER);
    const char *version = (const char *)glGetString(GL_VERSION);
    printf("sdl_backend=%s\ngl_vendor=%s\ngl_renderer=%s\ngl_version=%s\nglsl_version=%s\n",
           SDL_GetCurrentVideoDriver(), vendor, renderer, version, glGetString(GL_SHADING_LANGUAGE_VERSION));
    SDL_version sdl;
    SDL_GetVersion(&sdl);
    printf("sdl_version=%u.%u.%u\n", sdl.major, sdl.minor, sdl.patch);
    const struct { GLenum name; const char *label; } limits[] = {
        {GL_MAX_VERTEX_ATTRIBS, "max_vertex_attribs"}, {GL_MAX_VARYING_VECTORS, "max_varying_vectors"},
        {GL_MAX_VERTEX_UNIFORM_VECTORS, "max_vertex_uniform_vectors"},
        {GL_MAX_FRAGMENT_UNIFORM_VECTORS, "max_fragment_uniform_vectors"},
        {GL_MAX_TEXTURE_IMAGE_UNITS, "max_texture_units"}, {GL_MAX_TEXTURE_SIZE, "max_texture_size"},
    };
    for (size_t i = 0; i < sizeof limits / sizeof *limits; i++) {
        GLint n = 0; glGetIntegerv(limits[i].name, &n); printf("%s=%d\n", limits[i].label, n);
    }
    for (int stage = 0; stage < 2; stage++) {
        GLint range[2], bits;
        precision(stage ? GL_FRAGMENT_SHADER : GL_VERTEX_SHADER, GL_HIGH_FLOAT, range, &bits);
        printf("highp_%s=%d,%d,%d\n", stage ? "fragment" : "vertex", range[0], range[1], bits);
        if (bits < 23 || range[0] < 126 || range[1] < 127) return 0;
    }
    GLint n = 0; glGetIntegerv(GL_NUM_EXTENSIONS, &n);
    printf("gl_extensions_count=%d\n", n);
    for (int i = 0; i < n; i++) printf("gl_extension=%s\n", glGetStringi(GL_EXTENSIONS, i));
    void *egl = SDL_LoadObject("libEGL.so.1");
    if (!egl) return 0;
    void *(*current)(void) = SDL_LoadFunction(egl, "eglGetCurrentDisplay");
    const char *(*query)(void *, int) = SDL_LoadFunction(egl, "eglQueryString");
    void *display = current ? current() : NULL;
    if (!display || !query) { SDL_UnloadObject(egl); return 0; }
    printf("egl_vendor=%s\negl_version=%s\negl_client_apis=%s\negl_extensions=%s\n",
           query(display, 0x3053), query(display, 0x3054), query(display, 0x308D), query(display, 0x3055));
    SDL_UnloadObject(egl);
    int native = vendor && renderer && version && !strcmp(vendor, "ARM") &&
                 strstr(renderer, "Mali-G31") && strstr(version, "OpenGL ES 3.");
    int reference = desktop_reference() && !gl_es;
    FILE *maps = fopen("/proc/self/maps", "r"), *providers = fopen("graphics-providers.txt", "w");
    if (!maps || !providers) native = reference = 0;
    char line[2048];
    while (maps && fgets(line, sizeof line, maps)) {
        if (strstr(line, "libSDL") || strstr(line, "libEGL") || strstr(line, "libGLES") ||
            strstr(line, "Mali") || strstr(line, "mali") || strstr(line, "libGL") || strstr(line, "mesa")) {
            if (providers) fputs(line, providers);
            if (strstr(line, "GL4ES") || strstr(line, "gl4es")) native = reference = 0;
            if (strstr(line, "swrast")) native = 0;
        }
    }
    if (maps) fclose(maps);
    if (providers) fclose(providers);
    const char *overrides[] = {"MESA_GL_VERSION_OVERRIDE", "MESA_GLES_VERSION_OVERRIDE",
        "MESA_GLSL_VERSION_OVERRIDE", "LIBGL_ALWAYS_SOFTWARE", "LIBGL_ES", "LIBGL_GL"};
    for (size_t i = 0; i < sizeof overrides / sizeof *overrides; i++)
        if (getenv(overrides[i])) {
            if (reference && !strcmp(overrides[i], "LIBGL_ALWAYS_SOFTWARE"))
                printf("reference_override=%s\n", overrides[i]);
            else { printf("unsupported_override=%s\n", overrides[i]); native = reference = 0; }
        }
    printf("identity=%s\n", reference ? "DESKTOP_REFERENCE" : native ? "PASS" : "FAIL");
    return desktop_reference() ? reference : native;
}

int rt_gles_diagnostics(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    setenv("SH3_SHADER_DUMP", "1", 1);
    SDL_GLContext context = NULL;
    if (SDL_Init(SDL_INIT_VIDEO)) goto unavailable;
    gl_prepare_context();
    rt_window = SDL_CreateWindow("SH3 GLES diagnostics", SDL_WINDOWPOS_UNDEFINED,
                                 SDL_WINDOWPOS_UNDEFINED, 640, 480, SDL_WINDOW_OPENGL);
    if (!rt_window) goto unavailable;
    gl_context_open();
    context = SDL_GL_GetCurrentContext();
    puts("context_created=yes");
    int ok = identity();
    if (ok) {
        ok &= indexed_sample(); ok &= scissor_sample(); ok &= culling_sample();
        ok &= depth_sample(); ok &= stencil_sample(); ok &= precision_sample();
        ok &= rhw_depth_sample(); ok &= packed_color_sample(); ok &= presentation_sample();
    }
    printf("%s=%s\n", desktop_reference() ? "desktop_reference" : "gles", ok ? "PASS" : "FAIL");
    SDL_GL_DeleteContext(context);
    SDL_DestroyWindow(rt_window);
    SDL_Quit();
    return ok ? 0 : 9;
unavailable:
    fprintf(stderr, "GLES context unavailable: %s\n", SDL_GetError());
    if (rt_window) SDL_DestroyWindow(rt_window);
    SDL_Quit();
    return 9;
}
#endif
