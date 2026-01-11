FROM mambaorg/micromamba:1.5-bookworm-slim

USER root

# Create app directory
WORKDIR /app

# Copy pixi files
COPY pixi.toml pixi.lock* /app/

# Install pixi
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://pixi.sh/install.sh | bash && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.pixi/bin:${PATH}"

# Install dependencies
RUN pixi install

# Copy application code
COPY src/ /app/src/
COPY models/ /app/models/

# Expose port
EXPOSE 8000

# Run the server
CMD ["pixi", "run", "serve"]
