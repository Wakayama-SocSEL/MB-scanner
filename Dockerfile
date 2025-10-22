# ==============================================================================
# Base Image
# ==============================================================================
FROM debian:bookworm-slim

# ==============================================================================
# Arguments
# ==============================================================================
# ビルド時にホストマシンのUID/GID/USERNAMEを受け取る
ARG UID=1000
ARG GID=1000
ARG USERNAME=default
ARG UV_VERSION=latest

# ==============================================================================
# System Setup
# ==============================================================================
# --- Environment Variables ---
ENV DEBIAN_FRONTEND=noninteractive \
    # Python実行時の標準出力バッファリングを無効化（ログがリアルタイムで見える）
    PYTHONUNBUFFERED=1 \
    # .pycファイルの生成を無効化（イメージサイズ削減）
    PYTHONDONTWRITEBYTECODE=1

# --- Install System Dependencies ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- Install uv (system-wide) ---
ENV UV_INSTALL_DIR=/usr/local
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/usr/local:${PATH}"

# ==============================================================================
# CodeQL Setup
# ==============================================================================
ARG CODEQL_VERSION=latest

# --- Install Additional Dependencies for CodeQL ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        tar \
        git \
        unzip \
        ca-certificates \
        gnupg \
        procps \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- Install Node.js and npm for JavaScript analysis ---
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- Download and Install CodeQL CLI ---
RUN if [ "$CODEQL_VERSION" = "latest" ]; then \
        CODEQL_URL="https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip"; \
    else \
        CODEQL_URL="https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.zip"; \
    fi && \
    wget -q "$CODEQL_URL" -O /tmp/codeql.zip && \
    unzip -q /tmp/codeql.zip -d /opt && \
    rm /tmp/codeql.zip && \
    chmod -R 755 /opt/codeql

# --- Add CodeQL to PATH ---
ENV PATH="/opt/codeql:${PATH}"

# ==============================================================================
# User Setup
# ==============================================================================
# --- Create Non-root User ---
RUN if ! getent group ${GID} > /dev/null 2>&1; then \
        groupadd -g ${GID} ${USERNAME}; \
    fi && \
    useradd --uid ${UID} --gid ${GID} --create-home --shell /bin/bash ${USERNAME}

# --- Switch to Non-root User ---
USER ${USERNAME}

# --- Set Working Directory ---
WORKDIR /home/${USERNAME}/workspace

# --- Configure uv for user ---
ENV UV_CACHE_DIR=/home/${USERNAME}/.cache/uv \
    UV_PYTHON_PREFERENCE=only-managed

# キャッシュディレクトリを事前作成（権限問題の回避）
RUN mkdir -p ${UV_CACHE_DIR}
