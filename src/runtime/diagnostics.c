/* Native Linux runtime gate, independent of rendering and original assets. */
#ifndef __SWITCH__
#include "rt.h"
#include "host.h"
#include <stdatomic.h>
#include <errno.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <inttypes.h>
#include <time.h>
#include <unistd.h>

static long memory_kib(const char *key) {
    FILE *f = fopen("/proc/self/status", "r");
    char line[256];
    long value = -1;
    if (!f) return -1;
    while (fgets(line, sizeof line, f))
        if (!strncmp(line, key, strlen(key))) { sscanf(line + strlen(key), "%ld", &value); break; }
    fclose(f);
    return value;
}

static int diagnose_memory(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    long baseline_rss = memory_kib("VmRSS:"), baseline_vm = memory_kib("VmSize:");
    g_xbox_mem_offset = (ptrdiff_t)host_arena_reserve();
    long reserved_rss = memory_kib("VmRSS:"), reserved_vm = memory_kib("VmSize:");
    const uint32_t start = 0x10000000u, bytes = 8u << 20;
    host_arena_commit(start, bytes);
    host_arena_commit(0xFFFFF000u, 4096);
    volatile uint32_t *heap = GPTR(start), *top = GPTR(0xFFFFF000u);
    for (uint32_t i = 0; i < bytes / 4; i++) {
        if (heap[i]) { fprintf(stderr, "memory=FAIL initial pages not zero\n"); return 4; }
        heap[i] = i ^ 0x5A5AA5A5u;
    }
    for (uint32_t i = 0; i < bytes / 4; i++)
        if (heap[i] != (i ^ 0x5A5AA5A5u)) { fprintf(stderr, "memory=FAIL round trip\n"); return 4; }
    if (top[1023]) return 4;
    top[1023] = 0x12345678;
    if (top[1023] != 0x12345678 || (uintptr_t)&top[1023] - (uintptr_t)g_xbox_mem_offset != 0xFFFFFFFCull)
        return 4;
    long touched_rss = memory_kib("VmRSS:");
    printf("baseline_vm_kib=%ld reserved_vm_kib=%ld baseline_rss_kib=%ld reserved_rss_kib=%ld touched_rss_kib=%ld\n",
           baseline_vm, reserved_vm, baseline_rss, reserved_rss, touched_rss);
    if (baseline_rss < 0 || reserved_vm - baseline_vm < 4194304 ||
        reserved_rss - baseline_rss >= 4096 || touched_rss >= 131072) {
        fprintf(stderr, "memory=FAIL reservation/resident budget\n");
        return 4;
    }
    printf("memory=PASS arena_bytes=4294967296 committed_bytes=8392704 high_guest_va=FFFFFFFC\n");
    return 0;
}

typedef struct {
    atomic_int ready, request, completed, heartbeat, stop, finished;
    _Atomic(HostThread *) thread;
    uint32_t main_tib;
} Worker;

static uint64_t monotonic_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) return 0;
    return (uint64_t)ts.tv_sec * 1000000000ull + ts.tv_nsec;
}

static int await_value(atomic_int *value, int minimum) {
    uint64_t deadline = monotonic_ns() + 2000000000ull;
    while (atomic_load(value) < minimum) {
        if (atomic_load(value) < 0 || monotonic_ns() >= deadline) return 0;
        usleep(500);
    }
    return 1;
}

static void diagnostic_worker(void *arg) {
    Worker *w = arg;
    if (!g_fs_base || g_fs_base == w->main_tib || g_eax ||
        MEM32(g_fs_base + 0x18) != g_fs_base ||
        g_esp < MEM32(g_fs_base + 8) || g_esp >= MEM32(g_fs_base + 4)) {
        atomic_store(&w->ready, -1);
        return;
    }
    g_eax = 0x87654321;
    MEM32(g_esp) = 0x13572468;
    atomic_store(&w->thread, host_thread_self());
    atomic_store(&w->ready, 1);
    for (int round = 1; round <= 16; round++) {
        if (!await_value(&w->request, round)) { atomic_store(&w->completed, -1); return; }
        host_thread_pause(host_thread_self());
        atomic_store(&w->completed, round);
    }
    while (!atomic_load(&w->stop)) {
        atomic_fetch_add(&w->heartbeat, 1);
        usleep(500);
    }
    atomic_store(&w->finished, g_eax == 0x87654321 && MEM32(g_esp) == 0x13572468 ? 1 : -1);
}

static int diagnose_threads(void) {
    host_thread_adopt();
    rt_thread_init_main(1u << 20);
    uint32_t main_tib = g_fs_base, main_esp = g_esp;
    g_eax = 0x12345678;
    static Worker w;
    w.main_tib = main_tib;
    rt_spawn(diagnostic_worker, &w, 1u << 20);
    if (!await_value(&w.ready, 1)) { fprintf(stderr, "threads=FAIL guest TLS setup\n"); return 5; }
    HostThread *thread = atomic_load(&w.thread);
    for (int round = 1; round <= 16; round++) {
        host_thread_resume(thread);  /* deliberately arrives before worker's self pause */
        atomic_store(&w.request, round);
        if (!await_value(&w.completed, round)) { fprintf(stderr, "threads=FAIL queued wake\n"); return 5; }
    }
    if (!await_value(&w.heartbeat, 2)) return 5;
    for (int round = 0; round < 16; round++) {
        host_thread_pause(thread);  /* real SIGUSR2 handler on Linux */
        usleep(5000);
        int paused = atomic_load(&w.heartbeat);
        usleep(5000);
        if (paused != atomic_load(&w.heartbeat)) { fprintf(stderr, "threads=FAIL signal did not park worker\n"); return 5; }
        host_thread_resume(thread);
        if (!await_value(&w.heartbeat, paused + 1)) { fprintf(stderr, "threads=FAIL signal resume\n"); return 5; }
    }
    atomic_store(&w.stop, 1);
    if (!await_value(&w.finished, 1) || g_eax != 0x12345678 || g_fs_base != main_tib || g_esp != main_esp) {
        fprintf(stderr, "threads=FAIL guest state changed\n");
        return 5;
    }
    puts("threads=PASS tls=isolated resume_before_pause=16 signal_pause_resume=16");
    return 0;
}

static uintptr_t expected_fault;

static void diagnostic_fault(uintptr_t address) {
    char marker;
    stack_t stack;
    if (sigaltstack(NULL, &stack)) _exit(74);
    uintptr_t here = (uintptr_t)&marker, low = (uintptr_t)stack.ss_sp;
    _exit(address == expected_fault && (stack.ss_flags & SS_ONSTACK) &&
          here >= low && here - low < stack.ss_size ? 73 : 74);
}

static int diagnose_signals(void) {
    const uint32_t guards[] = {0x1000, 0x20000000};
    for (unsigned i = 0; i < sizeof guards / sizeof *guards; i++) {
        pid_t child = fork();
        if (child < 0) { perror("signals=FAIL fork"); return 6; }
        if (!child) {
            expected_fault = (uintptr_t)GPTR(guards[i]);
            host_crash_handlers(diagnostic_fault);
            *(volatile uint8_t *)expected_fault = 1;
            _exit(75);  /* an uncommitted page must fault */
        }
        int status;
        pid_t waited;
        do { waited = waitpid(child, &status, 0); } while (waited < 0 && errno == EINTR);
        if (waited != child || !WIFEXITED(status) || WEXITSTATUS(status) != 73) {
            fprintf(stderr, "signals=FAIL guest guard or alternate stack\n");
            return 6;
        }
    }
    puts("signals=PASS guard_faults=2 alternate_stack=yes");
    return 0;
}

extern const Bridge __start_game_bridges[], __stop_game_bridges[];

static uint32_t bridge_target(const char *name) {
    for (const Bridge *b = __start_game_bridges; b < __stop_game_bridges; b++)
        if (!strcmp(b->name, name)) return rt_host_fn(name, b->fn);
    fprintf(stderr, "timers=FAIL missing bridge %s\n", name);
    return 0;
}

static int timer_call(uint32_t target, int count, const uint32_t *args, uint32_t *result) {
    uint32_t saved_esp = g_esp;
    *result = guest_call(target, count, args, 1);
    return g_esp == saved_esp;
}

static uint64_t guest_u64(uint32_t address) {
    return MEM32(address) | (uint64_t)MEM32(address + 4) << 32;
}

static int diagnose_timers(void) {
    /* Same registered bridges and guest call ABI used by game's imported functions. */
    recomp_dispatch_init();
    uint32_t frequency = bridge_target("QueryPerformanceFrequency"), counter = bridge_target("QueryPerformanceCounter");
    uint32_t sleep_fn = bridge_target("Sleep"), tick_fn = bridge_target("GetTickCount"), multimedia_fn = bridge_target("timeGetTime");
    if (!frequency || !counter || !sleep_fn || !tick_fn || !multimedia_fn) return 7;
    uint32_t buffer = galloc(8), result, ticks_before, ticks_after, multimedia_before, multimedia_after;
    if (!timer_call(frequency, 1, &buffer, &result) || !result) return 7;
    uint64_t hz = guest_u64(buffer);
    if (!hz || !timer_call(counter, 1, &buffer, &result) || !result) return 7;
    uint64_t previous = guest_u64(buffer);
    for (int i = 0; i < 128; i++) {
        if (!timer_call(counter, 1, &buffer, &result) || !result || guest_u64(buffer) < previous) return 7;
        previous = guest_u64(buffer);
    }
    if (!timer_call(tick_fn, 0, NULL, &ticks_before) ||
        !timer_call(multimedia_fn, 0, NULL, &multimedia_before) ||
        !timer_call(counter, 1, &buffer, &result) || !result) return 7;
    uint64_t start = guest_u64(buffer);
    uint32_t milliseconds = 25;
    if (!timer_call(sleep_fn, 1, &milliseconds, &result) ||
        !timer_call(counter, 1, &buffer, &result) || !result) return 7;
    uint64_t end = guest_u64(buffer);
    if (!timer_call(tick_fn, 0, NULL, &ticks_after) ||
        !timer_call(multimedia_fn, 0, NULL, &multimedia_after) || end < start) return 7;
    uint64_t elapsed_us = (end - start) * 1000000ull / hz;
    uint32_t ticks_ms = ticks_after - ticks_before, multimedia_ms = multimedia_after - multimedia_before;
    if (elapsed_us < 20000 || elapsed_us >= 2000000 || ticks_ms < 20 || ticks_ms >= 2000 ||
        multimedia_ms < 20 || multimedia_ms >= 2000) {
        fprintf(stderr, "timers=FAIL sleep measurement\n");
        return 7;
    }
    printf("timers=PASS frequency_hz=%" PRIu64 " elapsed_us=%" PRIu64 " tick_delta_ms=%u multimedia_delta_ms=%u\n",
           hz, elapsed_us, ticks_ms, multimedia_ms);
    return 0;
}

int rt_runtime_diagnostics(void) {
    int status = diagnose_memory();
    if (!status) status = diagnose_signals();  /* fork while still single-threaded */
    if (!status) status = diagnose_threads();
    if (!status) status = diagnose_timers();
    if (!status) {
        struct rusage usage;
        long vm = memory_kib("VmSize:"), rss = memory_kib("VmRSS:");
        if (getrusage(RUSAGE_SELF, &usage) || vm < 4194304 || rss <= 0 || rss >= 131072 ||
            usage.ru_maxrss <= 0 || usage.ru_maxrss >= 131072) {
            fprintf(stderr, "memory=FAIL completed diagnostic session measurement\n");
            return 8;
        }
        printf("diagnostics_vm_kib=%ld diagnostics_rss_kib=%ld diagnostics_max_rss_kib=%ld\n",
               vm, rss, usage.ru_maxrss);
    }
    if (!status) puts("runtime=PASS rendering=untested");
    return status;
}
#endif
