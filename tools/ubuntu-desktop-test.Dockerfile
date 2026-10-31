ARG UBUNTU=24.04
FROM ubuntu:${UBUNTU}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 libdbus-1-3 libnss3 libnspr4 libasound2t64 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libgbm1 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libxtst6 libatspi2.0-0t64 libgtk-3-0t64 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 fonts-dejavu-core xvfb xauth python3 && rm -rf /var/lib/apt/lists/*
ENV QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software STOPOTS_RUNTIME=/runtime
WORKDIR /app
