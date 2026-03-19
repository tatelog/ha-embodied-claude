ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.20
FROM ${BUILD_FROM}

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-numpy \
    ffmpeg \
    git \
    curl \
    bash \
    ttyd \
    nodejs \
    npm \
    build-base \
    python3-dev \
    libffi-dev \
    musl-dev

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

# Copy run script and config
COPY rootfs /
COPY run.sh /
RUN chmod a+x /run.sh

WORKDIR /opt/embodied-claude

CMD [ "/run.sh" ]
