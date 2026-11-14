#pragma once
#include "gl.h"

/* Disposable driver cache. Exact generated sources remain fallback authority. */
int program_binary_load(GLuint program, const char *vertex, const char *fragment);
void program_binary_save(GLuint program, const char *vertex, const char *fragment);
