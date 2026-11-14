/* Linux diagnostic only: sample presenting thread's CPU, never a waiting thread.
 * Signal handler stores PC/frame in bounded memory; naming and I/O happen at exit. */
#define _GNU_SOURCE
#include "d3d8.h"
#include "profile.h"
#if defined(__linux__) && defined(__aarch64__)
#include <dlfcn.h>
#include <signal.h>
#include <sys/syscall.h>
#include <time.h>
#include <ucontext.h>
#include <unistd.h>

static struct { uintptr_t pc, caller; int frame; } samples[32768];
static volatile sig_atomic_t sample_count, sample_frame, dropped;
static timer_t sample_timer;
static FILE *sample_report;
static int sample_signal;

static void sample_cpu(int signo, siginfo_t *info, void *context) {
    (void)signo;
    ucontext_t *uc = context;
    sig_atomic_t i = sample_count;
    if (i < (sig_atomic_t)(sizeof samples / sizeof *samples)) {
        samples[i].pc = uc->uc_mcontext.pc;
        samples[i].caller = uc->uc_mcontext.regs[30];
        samples[i].frame = sample_frame;
        sample_count = i + 1;
    } else dropped++;
    if (info->si_overrun > 0) dropped += info->si_overrun;
}

static void finish_samples(void) {
    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, sample_signal);
    pthread_sigmask(SIG_BLOCK, &mask, NULL);
    timer_delete(sample_timer);
    fputs("frame,pc,module,offset,symbol,caller,caller_module,caller_offset\n", sample_report);
    int n = sample_count;
    for (int i = 0; i < n; i++) {
        uintptr_t pc = samples[i].pc;
        Dl_info info = {0}, caller = {0};
        dladdr((void *)pc, &info);
        dladdr((void *)samples[i].caller, &caller);
        fprintf(sample_report, "%d,%llx,%s,%llx,%s,%llx,%s,%llx\n", samples[i].frame,
                (unsigned long long)pc, info.dli_fname ? info.dli_fname : "unknown",
                (unsigned long long)(pc - (uintptr_t)info.dli_fbase),
                info.dli_sname ? info.dli_sname : "",
                (unsigned long long)samples[i].caller,
                caller.dli_fname ? caller.dli_fname : "unknown",
                (unsigned long long)(samples[i].caller - (uintptr_t)caller.dli_fbase));
    }
    int failed = ferror(sample_report);
    failed |= fclose(sample_report) != 0;
    rt_log("profile: CPU samples=%d dropped=%d interval_cpu_ms=10 write_failed=%d", n, (int)dropped, failed);
    /* Process is exiting; leave signal blocked so pending timer signal is harmless. */
}

void profile_cpu_frame(int frame) { sample_frame = frame; }

void profile_cpu_start(const char *path) {
    char *name;
    if (asprintf(&name, "%s.samples", path) < 0) return;
    sample_report = fopen(name, "w");
    free(name);
    if (!sample_report) { rt_log("profile: cannot open CPU sample report"); return; }
    sample_signal = SIGRTMIN + 6;
    struct sigaction old, action = {.sa_sigaction = sample_cpu, .sa_flags = SA_SIGINFO | SA_RESTART};
    sigemptyset(&action.sa_mask);
    if (sigaction(sample_signal, NULL, &old) != 0 || old.sa_handler != SIG_DFL) goto unavailable;
    if (sigaction(sample_signal, &action, NULL) != 0) goto unavailable;
    struct sigevent event = {.sigev_notify = SIGEV_THREAD_ID, .sigev_signo = sample_signal};
    event._sigev_un._tid = (pid_t)syscall(SYS_gettid);
    if (timer_create(CLOCK_THREAD_CPUTIME_ID, &event, &sample_timer) != 0) {
        sigaction(sample_signal, &old, NULL);
        goto unavailable;
    }
    struct itimerspec interval = {.it_value = {0, 10000000}, .it_interval = {0, 10000000}};
    if (timer_settime(sample_timer, 0, &interval, NULL) != 0) {
        timer_delete(sample_timer);
        sigaction(sample_signal, &old, NULL);
        goto unavailable;
    }
    atexit(finish_samples);
    profile_cpu_frame(rt_frame + 1);
    return;
unavailable:
    rt_log("profile: targeted CPU timer unavailable");
    fclose(sample_report);
    sample_report = NULL;
}
#else
void profile_cpu_start(const char *path) { (void)path; }
void profile_cpu_frame(int frame) { (void)frame; }
#endif
