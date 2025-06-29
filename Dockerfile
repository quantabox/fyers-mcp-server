FROM --platform=linux/amd64 python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb chromium-driver \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv

# Create cache directory with permissions
RUN mkdir -p /app/.cache/uv && chmod 777 /app/.cache/uv
ENV UV_CACHE_DIR=/app/.cache/uv

RUN uv sync --frozen

COPY . .

ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome

EXPOSE 8000

CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & exec uv run python fyers_mcp_full.py"]
