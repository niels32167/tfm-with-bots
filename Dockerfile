# The hosted server (ADR 0014): one image with the engine, the bots and their models, and the built GUI, served
# on one port. Built as the Hugging Face Space builds it (deploy/huggingface/make_space.sh), or by hand:
#   docker build -t terraforming-mars . && docker run --rm -p 7860:7860 terraforming-mars

# The GUI, built to static files.
FROM node:24-slim AS gui
WORKDIR /gui
COPY gui/package.json gui/package-lock.json ./
RUN npm ci
COPY gui/ ./
RUN npm run build

# The engine, built to a wheel.
FROM python:3.14-slim AS engine
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir "maturin>=1.15,<2"
WORKDIR /engine
COPY engine/ ./
RUN maturin build --release --out /wheels

# The server, run as the user Hugging Face Spaces run images as.
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY engine/pyproject.toml engine/
# The locked versions, without the CUDA packages torch's own wheel needs: the CPU build of torch is installed instead.
RUN uv export --frozen --no-dev --no-hashes --no-emit-package tm-engine --format requirements-txt -o locked.txt \
    && grep -v -E "^(nvidia-|cuda-|triton)" locked.txt > requirements.txt \
    && uv pip install --system --no-cache --torch-backend cpu -r requirements.txt
COPY --from=engine /wheels /wheels
RUN uv pip install --system --no-cache /wheels/*.whl
RUN useradd --create-home --uid 1000 user
COPY --chown=user . .
COPY --from=gui --chown=user /gui/dist gui/dist
USER user
EXPOSE 7860
# The free Space has 2 cores, though the process sees the host's: one bot thinks on each.
CMD ["python", "-m", "server", "--hosted", "--thinkers", "2", "--host", "0.0.0.0", "--port", "7860", "--gui", "gui/dist"]
