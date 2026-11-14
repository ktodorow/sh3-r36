/* Optional delayed GPU-region timing on context owner; never wait for results. */
#pragma once
#include "profile.h"
void profile_gpu_begin(void);
void profile_gpu_end(ProfileSwap frame);
void profile_gpu_stop(void);
