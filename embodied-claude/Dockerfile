ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm
FROM ${BUILD_FROM}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-dev \
    ffmpeg \
    git \
    curl \
    bash \
    jq \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd (web terminal)
RUN curl -fsSL -o /usr/local/bin/ttyd https://github.com/nicm/ttyd/releases/latest/download/ttyd.x86_64 && \
    chmod +x /usr/local/bin/ttyd

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Clone embodied-claude repository
RUN git clone --depth 1 https://github.com/lifemate-ai/embodied-claude.git /opt/embodied-claude

# Install each MCP server's dependencies
WORKDIR /opt/embodied-claude

RUN cd wifi-cam-mcp && uv sync && cd .. && \
    cd memory-mcp && uv sync && cd .. && \
    cd tts-mcp && uv sync && cd .. && \
    cd system-temperature-mcp && uv sync && cd ..

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

WORKDIR /opt/embodied-claude

CMD [ "/run.sh" ]
