/* Installed-launcher diagnostics. Never infer hardware support from host fixtures. */
#ifndef __SWITCH__
#include "d3d8.h"
#include <sys/resource.h>
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
    if (count) memcpy(args + 1, arguments, count * 4);
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

#ifdef SH3_GLES_SAMPLES
static int resource_capture(const char *name);
#endif

static int texture_format_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    const struct { uint32_t fmt, value; int bytes, r, g, b; const char *name; } cases[] = {
        {FMT_A8R8G8B8,0x33e02080,4,224,32,128,"argb8.ppm"},
        {FMT_X8R8G8B8,0x00e02080,4,224,32,128,"xrgb8.ppm"},
        {FMT_R5G6B5,0xf800,2,255,0,0,"rgb565.ppm"},
        {FMT_A1R5G5B5,0x83e0,2,0,255,0,"argb1555.ppm"},
        {FMT_X1R5G5B5,0x001f,2,0,0,255,"xrgb1555.ppm"},
        {FMT_A4R4G4B4,0x3f84,2,255,136,68,"argb4444.ppm"},
        {FMT_X4R4G4B4,0x0f84,2,255,136,68,"xrgb4444.ppm"},
    };
    uint32_t saved = dev->tex[0];
    dev->vs = 0x104;
    dev->ps = shader_create_ps(copy_guest(sample_ps, sizeof sample_ps));
    dev->rs[7] = dev->rs[27] = 0;
    int ok = 1;
    for (size_t c = 0; c < sizeof cases / sizeof *cases; c++) {
        dev->tex[0] = res_texture(2,2,1,0,cases[c].fmt,0,0);
        Res *t = res_of(dev->tex[0]), *s = res_of(t->surf[0][0]);
        for (int i = 0; i < 4; i++) memcpy(GPTR(s->mem + i * cases[c].bytes), &cases[c].value, cases[c].bytes);
        uint8_t original[16]; memcpy(original, GPTR(s->mem), s->size);
        t->dirty = s->dirty = 1;
        DEVICE(36,0,0,7,0xff000000,0x3f800000,0);
        DEVICE(72,5,2,copy_guest(sample_geometry,sizeof sample_geometry),24);
        ok &= resource_capture(cases[c].name) && pixel(32,24,cases[c].r,cases[c].g,cases[c].b);
        int alpha = cases[c].fmt == FMT_A8R8G8B8 || cases[c].fmt == FMT_A4R4G4B4 ? 51 : 255;
        ok &= frame[(24*64+32)*4+3] == alpha;
        ok &= !memcmp(original, GPTR(s->mem), s->size);
        GLenum error = glGetError();
        printf("texture_format=%u gl_error=%04x source_preserved=%s\n", cases[c].fmt,error,
               !memcmp(original,GPTR(s->mem),s->size) ? "yes" : "no");
        ok &= !error;
        res_release(t->obj);
    }
    dev->tex[0] = saved;
    printf("texture_formats=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

#ifdef SH3_GLES_SAMPLES
static int resource_capture(const char *name) {
    int ok = capture(name);
    char path[128]; snprintf(path, sizeof path, "%s.rgba", name);
    FILE *file = fopen(path, "wb");
    if (!file) return 0;
    ok &= fwrite(frame, 1, sizeof frame, file) == sizeof frame;
    fclose(file);
    GLenum error = glGetError();
    printf("resource_capture=%s gl_error=%04x\n", name, error);
    return ok && !error;
}

static int resource_draw(const char *name, float uv_scale) {
    float quad[24]; memcpy(quad, sample_geometry, sizeof quad);
    for (int i = 0; i < 4; i++) {
        quad[i*6+1] *= 48.f/64.f; /* Fit game's square quad to diagnostic target. */
        quad[i*6+4] *= uv_scale; quad[i*6+5] *= uv_scale;
    }
    uint32_t vertices = copy_guest(quad, sizeof quad);
    DEVICE(36,0,0,7,0xff000000,0x3f800000,0);
    uint32_t result = DEVICE(72,5,2,vertices,24);
    gfree(vertices);
    return !result && resource_capture(name);
}
#endif

static int palette_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    uint32_t saved = dev->tex[0], saved_palette = dev->cur_palette;
    dev->tex[0] = res_texture(2,2,1,0,FMT_P8,0,0);
    uint32_t locked = galloc(8), palette = galloc(1024);
    method(dev->tex[0],16,4,(uint32_t[]){0,locked,0,0});
    memset(GPTR(MEM32(locked+4)),1,4);
    method(dev->tex[0],17,1,(uint32_t[]){0});
    const struct { uint32_t index, entry; const char *name; int alpha; } cases[] = {
        {65535,0x338020e0,"palette-alpha.ppm",51},
        {65535,0xaa40c010,"palette-update.ppm",170},
        {65534,0x77605040,"palette-select.ppm",119},
        {65534,0x00604020,"palette-opaque.ppm",255},
    };
    int ok = 1;
    for (size_t i = 0; i < sizeof cases / sizeof *cases; i++) {
        memset(GPTR(palette),0,1024); MEM32(palette+4) = cases[i].entry;
        ok &= !DEVICE(66,cases[i].index,palette) && !DEVICE(68,cases[i].index);
        ok &= resource_draw(cases[i].name,1);
        ok &= frame[(24*64+32)*4+3] == cases[i].alpha;
    }
    Res *s = res_of(res_of(dev->tex[0])->surf[0][0]);
    ok &= !memcmp(GPTR(s->mem),(uint8_t[]){1,1,1,1},4);
    printf("palette_updates=%s source_preserved=%s\n",ok ? "PASS" : "FAIL",
           !memcmp(GPTR(s->mem),(uint8_t[]){1,1,1,1},4) ? "yes" : "no");
    res_release(dev->tex[0]); dev->tex[0] = saved; dev->cur_palette = saved_palette;
    gfree(locked); gfree(palette);
    return ok;
#endif
}

static int mip_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    uint32_t saved = dev->tex[0], locked = galloc(8);
    dev->tex[0] = res_texture(4,4,0,0,FMT_A8R8G8B8,0,0);
    const uint32_t colors[] = {0xffff0000,0xff00ff00,0xff0000ff};
    int ok = 1;
    for (uint32_t level = 0; level < 3; level++) {
        ok &= !method(dev->tex[0],16,4,(uint32_t[]){level,locked,0,0});
        uint32_t width = 4 >> level;
        for (uint32_t y = 0; y < width; y++) for (uint32_t x = 0; x < width; x++)
            MEM32(MEM32(locked+4) + y*MEM32(locked) + x*4) = colors[level];
        ok &= !method(dev->tex[0],17,1,(uint32_t[]){level});
    }
    dev->tss[0][18] = 1;
    ok &= resource_draw("mip-base.ppm",1) && pixel(32,24,255,0,0);
    ok &= resource_draw("mip-middle.ppm",32) && pixel(32,24,0,255,0);
    ok &= resource_draw("mip-tail.ppm",64) && pixel(32,24,0,0,255);
    ok &= !method(dev->tex[0],16,4,(uint32_t[]){1,locked,0,0});
    for (int i = 0; i < 4; i++) MEM32(MEM32(locked+4)+i*4) = 0xffffff00;
    ok &= !method(dev->tex[0],17,1,(uint32_t[]){1});
    ok &= resource_draw("mip-update.ppm",32) && pixel(32,24,255,255,0);
    dev->tss[0][18] = 0;
    res_release(dev->tex[0]); dev->tex[0] = saved; gfree(locked);
    printf("mip_updates=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int dxt_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    /* Literal block examples from S3TC encoding rules, not output of our decoder.
     * DXT3's reversed endpoints must still select four colors. */
    const struct { uint32_t fmt; uint8_t block[16]; const char *name; int x, rgba[4]; } cases[] = {
        {FMT_DXT1,{0,248,31,0,228,228,228,228},"dxt1.ppm",40,{170,0,85,255}},
        {FMT_DXT1,{31,0,0,248,228,228,228,228},"dxt1-alpha.ppm",56,{0,0,0,0}},
        {FMT_DXT3,{80,250,80,250,80,250,80,250,31,0,0,248,228,228,228,228},
            "dxt3.ppm",56,{170,0,85,255}},
        {FMT_DXT5,{255,0,136,142,232,136,142,232,224,7,0,0,0,0,0,0},
            "dxt5-eight.ppm",56,{0,255,0,36}},
        {FMT_DXT5,{0,255,190,234,171,190,234,171,224,7,0,0,0,0,0,0},
            "dxt5-six.ppm",56,{0,255,0,204}},
    };
    uint32_t saved = dev->tex[0], locked = galloc(8);
    int ok = 1;
    for (size_t i = 0; i < sizeof cases / sizeof *cases; i++) {
        dev->tex[0] = res_texture(4,4,1,0,cases[i].fmt,0,0);
        Res *s = res_of(res_of(dev->tex[0])->surf[0][0]);
        method(dev->tex[0],16,4,(uint32_t[]){0,locked,0,0});
        memcpy(GPTR(MEM32(locked+4)),cases[i].block,s->size);
        method(dev->tex[0],17,1,(uint32_t[]){0});
        int pass = resource_draw(cases[i].name,1);
        uint8_t *p = frame+(8*64+cases[i].x)*4;
        /* S3TC interpolation may quantize one UNORM8 step differently by GPU. */
        for (int c = 0; c < 4; c++) pass &= abs(p[c] - cases[i].rgba[c]) <= 1;
        int preserved = !memcmp(GPTR(s->mem),cases[i].block,s->size);
        printf("dxt_sample=%s result=%s source_preserved=%s\n",cases[i].name,
               pass ? "PASS" : "FAIL",preserved ? "yes" : "no");
        ok &= pass && preserved;
        res_release(dev->tex[0]);
    }
    dev->tex[0] = saved; gfree(locked);
    printf("dxt_variants=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int dxt_edge_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    const uint32_t formats[] = {FMT_DXT1,FMT_DXT3,FMT_DXT5};
    const uint16_t colors[] = {0xf800,0x07e0,0x001f,0xffe0};
    uint32_t saved = dev->tex[0], locked = galloc(8);
    int ok = 1;
    for (int c = 0; c < 3; c++) {
        dev->tex[0] = res_texture(7,5,0,0,formats[c],0,0);
        Res *t = res_of(dev->tex[0]);
        for (int level = 0; level < 3; level++) {
            Res *s = res_of(t->surf[0][level]);
            int block_size = c ? 16 : 8;
            method(t->obj,16,4,(uint32_t[]){level,locked,0,0});
            uint8_t *dst = GPTR(MEM32(locked+4));
            for (uint32_t b = 0; b < s->size / block_size; b++) {
                uint8_t *block = dst+b*block_size;
                memset(block,0,block_size);
                if (c == 1) memset(block,255,8);
                if (c == 2) block[0] = 255;
                uint16_t color = level == 0 ? colors[b] : level == 1 ? 0x001f : 0xf81f;
                memcpy(block+(c ? 8 : 0),&color,2);
            }
            method(t->obj,17,1,(uint32_t[]){level});
        }
        char name[64];
        snprintf(name,sizeof name,"dxt%d-tiles.ppm",c == 0 ? 1 : c == 1 ? 3 : 5);
        ok &= resource_draw(name,1) && pixel(8,8,255,0,0) && pixel(56,8,0,255,0);
        ok &= pixel(8,44,0,0,255) && pixel(56,44,255,255,0);
        dev->tss[0][18] = 1;
        snprintf(name,sizeof name,"dxt%d-tail.ppm",c == 0 ? 1 : c == 1 ? 3 : 5);
        ok &= resource_draw(name,64) && pixel(32,24,255,0,255);
        dev->tss[0][18] = 0;
        uint32_t rect = copy_guest((int32_t[]){0,0,4,4},16);
        method(t->obj,16,4,(uint32_t[]){0,locked,rect,0});
        uint16_t cyan = 0x07ff;
        memcpy(GPTR(MEM32(locked+4)+(c ? 8 : 0)),&cyan,2);
        method(t->obj,17,1,(uint32_t[]){0});
        Res *s = res_of(t->surf[0][0]); uint8_t original[64];
        memcpy(original,GPTR(s->mem),s->size);
        snprintf(name,sizeof name,"dxt%d-update.ppm",c == 0 ? 1 : c == 1 ? 3 : 5);
        ok &= resource_draw(name,1) && pixel(8,8,0,255,255) && pixel(56,44,255,255,0);
        ok &= !memcmp(original,GPTR(s->mem),s->size);
        res_release(t->obj); gfree(rect);
    }
    dev->tex[0] = saved; gfree(locked);
    printf("dxt_edges_updates=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int framebuffer_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    uint32_t saved_rt = dev->rt, saved_ds = dev->ds;
    res_addref(saved_rt); if (saved_ds) res_addref(saved_ds);
    memcpy(dev->palette[0]+1,(uint32_t[]){0xff0000ff,0xff00ff00,0xffff0000,0xff00ffff},16);
    dev->pal_version[0]++;
    uint32_t w = sample_rt_widths[1], h = sample_rt_heights[1];
    printf("sample_rt_table_va=006b1434 extent=%u,%u source_calls=00427ccc,00427d1a\n",w,h);
    uint32_t texture = res_texture(w,h,1,1,FMT_A8R8G8B8,0,0);
    uint32_t target = res_of(texture)->surf[0][0];
    uint32_t depth = res_surface(640,480,FMT_D24S8,0,1);
    int ok = !DEVICE(31,target,depth) && glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE;
    dev->rs[7] = dev->rs[14] = 1; dev->rs[23] = 4;
    dev->rs[52] = 1; dev->rs[53] = dev->rs[54] = dev->rs[55] = 1;
    dev->rs[56] = 3; dev->rs[57] = 7; dev->rs[58] = dev->rs[59] = 255;
    DEVICE(36,0,0,7,0xff000000,0x3f800000,7);
    float quad[24]; memcpy(quad,sample_geometry,sizeof quad);
    for (int i = 0; i < 4; i++) { quad[i*6] *= w/64.f; quad[i*6+1] *= h/64.f; }
    uint32_t vertices = copy_guest(quad,sizeof quad);
    ok &= !DEVICE(72,5,2,vertices,24); gfree(vertices);
    uint8_t *pixels = malloc((size_t)w*h*4);
    if (!pixels) rt_fatal("framebuffer capture allocation failed");
    glReadPixels(0,0,w,h,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
    FILE *file = fopen("framebuffer-512.ppm","wb");
    if (file) {
        fprintf(file,"P6\n%u %u\n255\n",w,h);
        for (uint32_t i = 0; i < w*h; i++) fwrite(pixels+i*4,1,3,file);
        ok &= !ferror(file); fclose(file);
    } else ok = 0;
    const int xy[][2] = {{128,128},{384,128},{128,500},{384,500}};
    const uint8_t rgb[][3] = {{255,0,0},{0,255,0},{0,0,255},{255,255,0}};
    for (int i = 0; i < 4; i++) ok &= !memcmp(pixels+((size_t)xy[i][1]*w+xy[i][0])*4,rgb[i],3);
    free(pixels);
    dev->rs[7] = dev->rs[52] = 0;
    DEVICE(31,saved_rt,saved_ds); res_release(texture); res_release(depth);

    uint32_t src = res_surface(64,48,FMT_A8R8G8B8,1,0);
    uint32_t dst = res_surface(64,48,FMT_A8R8G8B8,1,0);
    uint32_t image = res_surface(70,50,FMT_A8R8G8B8,0,0);
    DEVICE(31,src,saved_ds);
    ok &= resource_draw("copy-source.ppm",1);
    ok &= !DEVICE(28,src,0,0,dst,0);
    DEVICE(31,dst,saved_ds); ok &= resource_capture("copy-gpu.ppm");
    Res *cpu = res_of(image); memset(GPTR(cpu->mem),0xcd,cpu->size);
    uint32_t rect = copy_guest((int32_t[]){4,6,60,42},16);
    uint32_t point = copy_guest((int32_t[]){3,1},8);
    ok &= !DEVICE(28,src,rect,1,image,point);
    ok &= MEM32(cpu->mem) == 0xcdcdcdcd && MEM32(cpu->mem+cpu->size-4) == 0xcdcdcdcd;
    ok &= MEM32(cpu->mem+3*cpu->pitch+7*4) == 0xffff0000;
    memcpy(GPTR(rect),(int32_t[]){3,1,59,37},16); memcpy(GPTR(point),(int32_t[]){4,6},8);
    DEVICE(36,0,0,1,0xff000000,0x3f800000,0);
    ok &= !DEVICE(28,image,rect,1,dst,point);
    ok &= resource_capture("copy-upload.ppm") && pixel(8,8,255,0,0) && pixel(48,36,255,255,0) && pixel(2,2,0,0,0);
    uint32_t locked = galloc(8);
    for (int pass = 0; pass < 2; pass++) {
        uint32_t color = pass ? 0xffff0000 : 0xff0000ff;
        DEVICE(36,0,0,1,color,0x3f800000,0);
        ok &= !method(dst,9,3,(uint32_t[]){locked,0,0x10});
        int fresh = MEM32(MEM32(locked+4)) == color;
        ok &= fresh; method(dst,10,0,NULL);
        printf("readback_repeat=%d fresh=%s\n",pass,fresh ? "yes" : "no");
    }
    const struct { uint32_t fmt, packed; int bytes; } formats[] = {
        {FMT_A8R8G8B8,0xffff0000,4},{FMT_R5G6B5,0xf800,2},
        {FMT_A1R5G5B5,0xfc00,2},{FMT_A4R4G4B4,0xff00,2},
    };
    for (size_t i = 0; i < sizeof formats / sizeof *formats; i++) {
        uint32_t surface = res_surface(64,48,formats[i].fmt,1,0);
        DEVICE(31,surface,0); DEVICE(36,0,0,1,0xffff0000,0x3f800000,0);
        method(surface,9,3,(uint32_t[]){locked,0,0x10});
        uint32_t value = 0; memcpy(&value,GPTR(MEM32(locked+4)),formats[i].bytes);
        method(surface,10,0,NULL);
        GLenum error = glGetError();
        printf("readback_format=%u value=%08x gl_error=%04x\n",formats[i].fmt,value,error);
        ok &= value == formats[i].packed && !error;
        DEVICE(31,saved_rt,saved_ds); res_release(surface);
    }
    DEVICE(31,saved_rt,saved_ds);
    res_release(src); res_release(dst); res_release(image);
    res_release(saved_rt); if (saved_ds) res_release(saved_ds);
    gfree(rect); gfree(point); gfree(locked);
    GLenum error = glGetError();
    printf("framebuffer_roundtrip=%s gl_error=%04x\n",ok && !error ? "PASS" : "FAIL",error);
    return ok && !error;
#endif
}

static int front_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    uint32_t saved_tex = dev->tex[0], saved_ps = dev->ps;
    int ok = resource_draw("front-source.ppm",1) && !DEVICE(15,0,0,0,0);
    DEVICE(36,0,0,1,0xffff00ff,0x3f800000,0); /* Next backbuffer must not replace front. */
    uint32_t image = res_surface(70,50,FMT_A8R8G8B8,0,0);
    Res *cpu = res_of(image); memset(GPTR(cpu->mem),0xcd,cpu->size);
    ok &= !DEVICE(30,image);
    const int xy[][2] = {{16,12},{48,12},{16,36},{48,36}};
    const uint32_t colors[] = {0xffff0000,0xff00ff00,0xff0000ff,0xffffff00};
    for (int i = 0; i < 4; i++) ok &= MEM32(cpu->mem+xy[i][1]*cpu->pitch+xy[i][0]*4) == colors[i];
    int untouched = MEM32(cpu->mem+64*4) == 0xcdcdcdcd && MEM32(cpu->mem+48*cpu->pitch) == 0xcdcdcdcd;
    ok &= untouched;
    printf("front_snapshot=last-presented outside_untouched=%s\n",untouched ? "yes" : "no");
    dev->tex[0] = res_texture(64,48,1,0,FMT_A8R8G8B8,0,0);
    uint32_t surface = res_of(dev->tex[0])->surf[0][0];
    uint32_t rect = copy_guest((int32_t[]){0,0,64,48},16);
    ok &= !DEVICE(28,image,rect,1,surface,0);
    uint32_t states[TSS_COUNT]; memcpy(states,dev->tss[0],sizeof states);
    dev->ps = 0; dev->rs[27] = 1; dev->rs[19] = 5; dev->rs[20] = 6;
    dev->rs[60] = 0x80ffffff; dev->tss[0][4] = 2; dev->tss[0][5] = 3;
    ok &= resource_draw("front-preview.ppm",1);
    const uint8_t rgb[][3] = {{128,0,0},{0,128,0},{0,0,128},{128,128,0}};
    for (int i = 0; i < 4; i++) for (int c = 0; c < 3; c++)
        ok &= abs(frame[(xy[i][1]*64+xy[i][0])*4+c]-rgb[i][c]) <= 1;
    dev->rs[27] = 0; dev->rs[19] = 2; dev->rs[20] = 1; dev->rs[60] = 0xffffffff;
    memcpy(dev->tss[0],states,sizeof states);
    res_release(dev->tex[0]); dev->tex[0] = saved_tex; dev->ps = saved_ps;
    res_release(image); gfree(rect);
    printf("front_preview=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int sampler_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    const struct { const char *name; uint32_t mode, filter; float u; int rgb[3]; } cases[] = {
        {"wrap",1,1,-.25f,{0,255,0}}, {"mirror",2,1,-.25f,{255,0,0}},
        {"edge",3,1,-.25f,{255,0,0}}, {"border",4,1,-.25f,{0,0,255}},
        {"border-linear",4,2,0,{128,0,128}}, {"linear",3,2,.5f,{128,128,0}},
    };
    uint32_t states[TSS_COUNT]; memcpy(states,dev->tss[0],sizeof states);
    int ok = 1;
    for (size_t i = 0; i < sizeof cases / sizeof *cases; i++) {
        dev->tss[0][13] = dev->tss[0][14] = cases[i].mode;
        dev->tss[0][16] = dev->tss[0][17] = cases[i].filter;
        dev->tss[0][15] = 0xff0000ff;
        float quad[24]; memcpy(quad,sample_geometry,sizeof quad);
        for (int v = 0; v < 4; v++) {
            quad[v*6+1] *= 48.f/64.f;
            quad[v*6+4] = cases[i].u; quad[v*6+5] = .25f;
        }
        DEVICE(36,0,0,7,0xff000000,0x3f800000,0);
        uint32_t vertices = copy_guest(quad,sizeof quad);
        ok &= !DEVICE(72,5,2,vertices,24); gfree(vertices);
        char name[64]; snprintf(name,sizeof name,"sampler-%s.ppm",cases[i].name);
        int pass = resource_capture(name);
        for (int c = 0; c < 3; c++) pass &= abs(frame[(24*64+32)*4+c]-cases[i].rgb[c]) <= 1;
        printf("sampler=%s result=%s\n",cases[i].name,pass ? "PASS" : "FAIL");
        ok &= pass;
    }
    memcpy(dev->tss[0],states,sizeof states);
    printf("samplers=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int resource_memory_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    const uint32_t formats[] = {FMT_A8R8G8B8,FMT_R5G6B5,FMT_A1R5G5B5,FMT_A4R4G4B4,
                               FMT_P8,FMT_DXT1,FMT_DXT3,FMT_DXT5};
    uint32_t saved = dev->tex[0];
    int ok = 1;
    for (size_t i = 0; i < sizeof formats / sizeof *formats; i++) {
        dev->tex[0] = res_texture(512,512,0,0,formats[i],0,0);
        Res *t = res_of(dev->tex[0]);
        for (uint32_t l = 0; l < t->levels; l++) {
            Res *s = res_of(t->surf[0][l]);
            memset(GPTR(s->mem),0,s->size); s->dirty = 1;
        }
        t->dirty = 1;
        char name[64]; snprintf(name,sizeof name,"memory-%u.ppm",formats[i]);
        ok &= resource_draw(name,1) && pixel(32,24,0,0,0);
        res_release(t->obj);
    }
    dev->tex[0] = saved;
    struct rusage usage = {0};
    ok &= !getrusage(RUSAGE_SELF,&usage);
    printf("graphics_peak_rss_kib=%ld\nresource_memory=%s\n",usage.ru_maxrss,ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int locked_target_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    uint32_t saved_rt = dev->rt, saved_ds = dev->ds;
    res_addref(saved_rt); if (saved_ds) res_addref(saved_ds);
    uint32_t target = res_surface(64,48,FMT_A8R8G8B8,1,0);
    uint32_t image = res_surface(64,48,FMT_A8R8G8B8,0,0), locked = galloc(8);
    DEVICE(31,target,0); DEVICE(36,0,0,1,0xff00ff00,0x3f800000,0);
    method(target,9,3,(uint32_t[]){locked,0,0x10}); method(target,10,0,NULL);
    Res *cpu = res_of(image);
    for (uint32_t i = 0; i < cpu->size; i += 4) MEM32(cpu->mem+i) = 0xff0000ff;
    int ok = !DEVICE(28,image,0,0,target,0);
    ok &= resource_capture("copy-after-lock.ppm") && pixel(48,36,0,0,255);
    uint32_t rect = copy_guest((int32_t[]){0,0,16,16},16);
    ok &= !method(target,9,3,(uint32_t[]){locked,rect,0});
    for (int y = 0; y < 16; y++) for (int x = 0; x < 16; x++)
        MEM32(MEM32(locked+4)+y*MEM32(locked)+x*4) = 0xffffff00;
    ok &= !method(target,10,0,NULL);
    ok &= resource_capture("locked-target-update.ppm") && pixel(8,8,255,255,0) && pixel(48,36,0,0,255);
    DEVICE(31,saved_rt,saved_ds);
    res_release(target); res_release(image); res_release(saved_rt); if (saved_ds) res_release(saved_ds);
    gfree(locked); gfree(rect);
    printf("locked_target_update=%s\n",ok ? "PASS" : "FAIL");
    return ok;
#endif
}

static int compressed_copy_sample(void) {
#ifndef SH3_GLES_SAMPLES
    return 0;
#else
    const uint32_t formats[] = {FMT_DXT1,FMT_DXT3,FMT_DXT5};
    uint32_t saved = dev->tex[0];
    int ok = 1;
    for (int i = 0; i < 3; i++) {
        uint32_t source = res_surface(1,1,formats[i],0,0);
        Res *s = res_of(source); uint8_t *block = GPTR(s->mem);
        memset(block,0,s->size);
        if (i == 1) memset(block,255,8);
        if (i == 2) block[0] = 255;
        uint16_t magenta = 0xf81f; memcpy(block+(i ? 8 : 0),&magenta,2);
        dev->tex[0] = res_texture(1,1,1,0,formats[i],0,0);
        uint32_t destination = res_of(dev->tex[0])->surf[0][0];
        ok &= !DEVICE(28,source,0,0,destination,0);
        char name[64]; snprintf(name,sizeof name,"dxt%d-copy-tail.ppm",i == 0 ? 1 : i == 1 ? 3 : 5);
        ok &= resource_draw(name,1) && pixel(32,24,255,0,255);
        res_release(source); res_release(dev->tex[0]);
    }
    dev->tex[0] = saved;
    printf("compressed_copy_tail=%s\n",ok ? "PASS" : "FAIL");
    return ok;
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
    glGetIntegerv(GL_NUM_COMPRESSED_TEXTURE_FORMATS, &n);
    GLint *formats = calloc(n ? n : 1, sizeof *formats);
    glGetIntegerv(GL_COMPRESSED_TEXTURE_FORMATS, formats);
    for (int i = 0; i < n; i++) printf("compressed_format=%04x\n",formats[i]);
    free(formats);
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
    setenv("SH3_RESOURCE_DUMP", "1", 1);
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
        ok &= rhw_depth_sample(); ok &= packed_color_sample();
        ok &= texture_format_sample(); ok &= palette_sample(); ok &= mip_sample();
        ok &= dxt_sample(); ok &= dxt_edge_sample();
        ok &= framebuffer_sample();
        ok &= front_sample();
        ok &= sampler_sample();
        ok &= resource_memory_sample();
        ok &= locked_target_sample();
        ok &= compressed_copy_sample();
        ok &= presentation_sample();
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
