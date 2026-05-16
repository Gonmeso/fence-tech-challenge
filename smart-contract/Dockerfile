FROM ghcr.io/foundry-rs/foundry:stable

WORKDIR /app

COPY foundry.toml ./
COPY src ./src
COPY script ./script
COPY lib ./lib
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN forge build

EXPOSE 8545

HEALTHCHECK --interval=5s --timeout=5s --start-period=10s --retries=30 \
  CMD cast code "${CONTRACT_ADDRESS:-0x5FbDB2315678afecb367f032d93F642f64180aa3}" --rpc-url "http://127.0.0.1:${ANVIL_PORT:-8545}" | grep -vq '^0x$'

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
