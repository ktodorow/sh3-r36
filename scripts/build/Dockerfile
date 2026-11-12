FROM debian@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
LABEL org.sh3-r36s.build="native-arm64"
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261111T000000Z/ bookworm main\n' > /etc/apt/sources.list && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261111T000000Z/ bookworm-security main\n' >> /etc/apt/sources.list && \
    apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get install -y --no-install-recommends build-essential cmake ninja-build \
        python3 python3-venv libsdl2-dev pkg-config file ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/sh3-python && \
    /opt/sh3-python/bin/pip install --no-cache-dir --only-binary=:all: capstone==5.0.6
ENV SH3_PYTHON=/opt/sh3-python/bin/python3
WORKDIR /work
