#include "d3d8.h"
#include "profile.h"
#include <time.h>

static FILE *report;
static int checked;
static double counter_ms, previous_cpu;
static uint64_t previous_frame, draw_ticks, buffer_bytes;
static unsigned draws;

static double thread_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &t);
    return t.tv_sec * 1000.0 + t.tv_nsec / 1000000.0;
}

uint64_t profile_stamp(void) {
    if (!checked) {
        checked = 1;
        const char *path = getenv("SH3_PROFILE");
        if (path && *path) {
            report = fopen(path, "w");
            if (!report) rt_log("profile: cannot open requested report");
            else {
                static char buffer[65536];
                setvbuf(report, buffer, _IOFBF, sizeof buffer);
                counter_ms = 1000.0 / SDL_GetPerformanceFrequency();
                fputs("frame,elapsed_ms,wall_ms,cpu_ms,draw_ms,present_ms,swap_ms,draws,buffer_bytes,room,internal_w,internal_h\n", report);
                profile_cpu_start(path);
            }
        }
    }
    return report ? SDL_GetPerformanceCounter() : 0;
}

void profile_draw_end(uint64_t start) {
    if (!start) return;
    draw_ticks += SDL_GetPerformanceCounter() - start;
    draws++;
}

void profile_buffer_upload(uint32_t bytes) {
    if (report) buffer_bytes += bytes;
}

ProfileSwap profile_swap_snapshot(void) {
    if (!report) return (ProfileSwap){0};
    return (ProfileSwap){1, rt_frame, MEM32(0x72D2C0), MEM32(0x72BFD0), MEM32(0x72BFD4)};
}

void profile_swap_end(ProfileSwap frame, uint64_t start) {
    if (!start) return;
    uint64_t end = SDL_GetPerformanceCounter();
    uint64_t elapsed = SDL_GetTicks64();
    static FILE *presents;
    static int initialized;
    static uint64_t previous;
    static double milliseconds;
    if (!initialized) {
        initialized = 1;
        const char *path = getenv("SH3_PROFILE");
        char *name = malloc(strlen(path) + sizeof ".presents.csv");
        if (name) {
            strcpy(name, path);
            strcat(name, ".presents.csv");
            presents = fopen(name, "w");
            free(name);
        }
        if (!presents) rt_log("profile: cannot open swap completion report");
        else {
            static char buffer[65536];
            setvbuf(presents, buffer, _IOFBF, sizeof buffer);
            milliseconds = 1000.0 / SDL_GetPerformanceFrequency();
            fputs("frame,elapsed_ms,wall_ms,swap_ms,room,internal_w,internal_h\n", presents);
        }
    }
    if (!presents) return;
    fprintf(presents, "%d,%llu,%.6f,%.6f,%u,%u,%u\n", frame.frame,
            (unsigned long long)elapsed, previous ? (end - previous) * milliseconds : 0,
            (end - start) * milliseconds, frame.room, frame.width, frame.height);
    previous = end;
    if (frame.frame % 120 == 0) fflush(presents);
    if (ferror(presents)) {
        rt_log("profile: swap completion report write failed");
        fclose(presents);
        presents = NULL;
    }
}

void profile_present(uint64_t start, uint64_t swap_start) {
    if (!start) return;
    uint64_t end = SDL_GetPerformanceCounter();
    double cpu = thread_ms();
    if (previous_frame) {
        fprintf(report, "%d,%llu,%.6f,%.6f,%.6f,%.6f,%.6f,%u,%llu,%u,%u,%u\n",
                rt_frame, (unsigned long long)SDL_GetTicks64(),
                (end - previous_frame) * counter_ms, cpu - previous_cpu, draw_ticks * counter_ms,
                (end - start) * counter_ms, (end - swap_start) * counter_ms,
                draws, (unsigned long long)buffer_bytes,
                MEM32(0x72D2C0), MEM32(0x72BFD0), MEM32(0x72BFD4));
        /* Bound evidence lost on abnormal exit without flushing every frame. */
        if (rt_frame % 120 == 0) fflush(report);
        if (ferror(report)) {
            rt_log("profile: report write failed");
            fclose(report);
            report = NULL;
        }
    }
    previous_frame = end;
    previous_cpu = cpu;
    draw_ticks = buffer_bytes = draws = 0;
    profile_cpu_frame(rt_frame + 1);
}
