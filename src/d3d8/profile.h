/* Optional CPU-side timings; no GPU flush, query or pixel readback. */
#pragma once
#include <stdint.h>

uint64_t profile_stamp(void);
void profile_draw_end(uint64_t start);
void profile_buffer_upload(uint32_t bytes);
void profile_present(uint64_t start, uint64_t swap_start);
/* Capture guest metadata on producer; only worker owns completion report. */
typedef struct ProfileSwap {
    int enabled, frame;
    uint32_t room, width, height;
} ProfileSwap;
ProfileSwap profile_swap_snapshot(void);
void profile_swap_end(ProfileSwap frame, uint64_t start);
void profile_cpu_start(const char *path);
void profile_cpu_frame(int frame);
