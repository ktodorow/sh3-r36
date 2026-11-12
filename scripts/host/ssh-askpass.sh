#!/bin/sh
# SSH consumes stdout privately; caller never logs askpass output.
printf '%s\n' "$R36S_SSH_PASSWORD"
