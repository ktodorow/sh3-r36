#include "program_binary.h"
#include "../runtime/rt.h"

#define CACHE_FILE "sh3-gl-cache.bin"
#define CACHE_MAGIC 0x53484231u
#define CACHE_LIMIT (32u * 1024 * 1024)
#define SOURCE_LIMIT (1024u * 1024)
#define BINARY_LIMIT (4u * 1024 * 1024)
typedef struct { uint32_t vertex, fragment, binary, format, checksum; } BinaryRecord;
static unsigned char *cache;
static size_t cache_size, records_at, file_size;
static char *fingerprint;
static uint32_t fingerprint_size;
static GLint formats[64], format_count;
static int initialized, enabled, append;
static unsigned restored, missed, written, rejected;

static uint32_t checksum(const BinaryRecord *record, const void *payload) {
    uint32_t h = 2166136261u;
    const unsigned char *data = (const void *)record;
    for (size_t i = 0; i < 4 * sizeof(uint32_t); i++) h = (h ^ data[i]) * 16777619u;
    data = payload;
    size_t bytes = (size_t)record->vertex + record->fragment + record->binary;
    for (size_t i = 0; i < bytes; i++) h = (h ^ data[i]) * 16777619u;
    return h;
}
static int record_at(size_t offset, BinaryRecord *record) {
    if (cache_size - offset < sizeof *record) return 0;
    memcpy(record, cache + offset, sizeof *record);
    size_t bytes = (size_t)record->vertex + record->fragment + record->binary;
    return record->vertex && record->vertex <= SOURCE_LIMIT &&
        record->fragment && record->fragment <= SOURCE_LIMIT &&
        record->binary && record->binary <= BINARY_LIMIT &&
        bytes <= cache_size - offset - sizeof *record &&
        record->checksum == checksum(record, cache + offset + sizeof *record);
}
static void report(void) {
    if (getenv("SH3_PROFILE"))
        rt_log("program binaries: restored=%u missed=%u written=%u rejected=%u",
               restored, missed, written, rejected);
    free(cache); free(fingerprint);
}
static void initialize(void) {
    if (initialized) return;
    initialized = 1;
    if (!glProgramBinary || !glGetProgramBinary || !glProgramParameteri) return;
    glGetIntegerv(GL_NUM_PROGRAM_BINARY_FORMATS, &format_count);
    if (format_count <= 0 || format_count > 64) return;
    glGetIntegerv(GL_PROGRAM_BINARY_FORMATS, formats);
    const GLenum fields[] = {GL_VENDOR, GL_RENDERER, GL_VERSION, GL_SHADING_LANGUAGE_VERSION};
    const char *strings[4];
    size_t bytes = 1024;
    for (unsigned i = 0; i < 4; i++) {
        strings[i] = (const char *)glGetString(fields[i]);
        if (!strings[i] || strlen(strings[i]) > 4096) return;
        bytes += strlen(strings[i]) + 1;
    }
    fingerprint = malloc(bytes);
    if (!fingerprint) return;
    size_t used = 0;
    for (unsigned i = 0; i < 4; i++) {
        size_t length = strlen(strings[i]) + 1;
        memcpy(fingerprint + used, strings[i], length); used += length;
    }
    for (int i = 0; i < format_count; i++) {
        memcpy(fingerprint + used, &formats[i], sizeof formats[i]); used += sizeof formats[i];
    }
    fingerprint_size = used;
    records_at = 2 * sizeof(uint32_t) + used;
    enabled = 1;
    atexit(report);
    FILE *file = fopen(CACHE_FILE, "rb");
    if (!file) return;
    if (fseek(file, 0, SEEK_END)) { fclose(file); return; }
    long length = ftell(file);
    if (length < (long)records_at || length > CACHE_LIMIT || fseek(file, 0, SEEK_SET)) {
        fclose(file); return;
    }
    cache = malloc(length);
    if (!cache) { fclose(file); return; }
    cache_size = length;
    int valid = fread(cache, 1, cache_size, file) == cache_size;
    fclose(file);
    uint32_t header[2]; memcpy(header, cache, sizeof header);
    valid = valid && header[0] == CACHE_MAGIC && header[1] == used &&
        !memcmp(cache + sizeof header, fingerprint, used);
    for (size_t offset = records_at; valid && offset < cache_size;) {
        BinaryRecord record;
        valid = record_at(offset, &record);
        if (valid) offset += sizeof record + record.vertex + record.fragment + record.binary;
    }
    if (!valid) { free(cache); cache = NULL; cache_size = 0; return; }
    file_size = cache_size; append = 1;
}

int program_binary_load(GLuint program, const char *vertex, const char *fragment) {
    initialize();
    if (!enabled) return 0;
    size_t v = strlen(vertex), f = strlen(fragment);
    for (size_t offset = records_at; offset < cache_size;) {
        BinaryRecord record; memcpy(&record, cache + offset, sizeof record);
        const unsigned char *data = cache + offset + sizeof record;
        if (record.vertex == v && record.fragment == f && !memcmp(data, vertex, v) &&
            !memcmp(data + v, fragment, f)) {
            int supported = 0;
            for (int i = 0; i < format_count; i++) supported |= (uint32_t)formats[i] == record.format;
            if (supported) {
                glProgramBinary(program, record.format, data + v + f, record.binary);
                GLint linked = GL_FALSE;
                glGetProgramiv(program, GL_LINK_STATUS, &linked);
                if (linked) { restored++; return 1; }
                while (glGetError() != GL_NO_ERROR) { }
                rejected++;
            }
            break;
        }
        offset += sizeof record + record.vertex + record.fragment + record.binary;
    }
    missed++;
    return 0;
}

void program_binary_save(GLuint program, const char *vertex, const char *fragment) {
    if (!enabled) return;
    GLint length = 0;
    glGetProgramiv(program, GL_PROGRAM_BINARY_LENGTH, &length);
    size_t v = strlen(vertex), f = strlen(fragment);
    if (length <= 0 || length > BINARY_LIMIT || v > SOURCE_LIMIT || f > SOURCE_LIMIT ||
        sizeof(BinaryRecord) + v + f + length + records_at > CACHE_LIMIT - file_size) return;
    unsigned char *payload = malloc(v + f + length);
    if (!payload) return;
    memcpy(payload, vertex, v); memcpy(payload + v, fragment, f);
    GLsizei bytes = 0; GLenum format = 0;
    glGetProgramBinary(program, length, &bytes, &format, payload + v + f);
    if (bytes > 0 && bytes <= length) {
        BinaryRecord record = {v, f, bytes, format, 0};
        record.checksum = checksum(&record, payload);
        FILE *file = fopen(CACHE_FILE, append ? "ab" : "wb");
        if (file) {
            uint32_t header[2] = {CACHE_MAGIC, fingerprint_size};
            int ok = append || (fwrite(header, sizeof header, 1, file) == 1 &&
                fwrite(fingerprint, 1, fingerprint_size, file) == fingerprint_size);
            size_t count = v + f + bytes;
            ok = ok && fwrite(&record, sizeof record, 1, file) == 1 &&
                fwrite(payload, 1, count, file) == count;
            ok &= fclose(file) == 0;
            if (ok) {
                if (!append) file_size = records_at;
                file_size += sizeof record + count; append = 1; written++;
            } else enabled = 0;
        }
    }
    free(payload);
}
