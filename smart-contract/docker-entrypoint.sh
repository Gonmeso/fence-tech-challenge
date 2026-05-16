#!/usr/bin/env sh
set -eu

ANVIL_HOST="${ANVIL_HOST:-0.0.0.0}"
ANVIL_PORT="${ANVIL_PORT:-8545}"
ANVIL_CHAIN_ID="${ANVIL_CHAIN_ID:-31337}"
RPC_URL="http://127.0.0.1:${ANVIL_PORT}"
PRIVATE_KEY="${PRIVATE_KEY:?PRIVATE_KEY is required}"
CONTRACT_ADDRESS="${CONTRACT_ADDRESS:-0x5FbDB2315678afecb367f032d93F642f64180aa3}"

cleanup() {
  if [ -n "${ANVIL_PID:-}" ]; then
    kill "$ANVIL_PID" >/dev/null 2>&1 || true
  fi
}

wait_for_rpc() {
  attempts=0
  until cast chain-id --rpc-url "$RPC_URL" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 60 ]; then
      echo "Anvil did not become ready at $RPC_URL" >&2
      return 1
    fi
    sleep 0.5
  done
}

wait_for_contract() {
  attempts=0
  until [ "$(cast code "$CONTRACT_ADDRESS" --rpc-url "$RPC_URL")" != "0x" ]; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 60 ]; then
      echo "Contract code was not found at $CONTRACT_ADDRESS" >&2
      return 1
    fi
    sleep 0.5
  done
}

trap cleanup INT TERM

anvil --host "$ANVIL_HOST" --port "$ANVIL_PORT" --chain-id "$ANVIL_CHAIN_ID" &
ANVIL_PID="$!"

wait_for_rpc

PRIVATE_KEY="$PRIVATE_KEY" forge script \
  script/Deploy.s.sol:DeployFacilityCovenantRegistry \
  --rpc-url "$RPC_URL" \
  --broadcast

wait_for_contract

echo "FacilityCovenantRegistry deployed at $CONTRACT_ADDRESS"

wait "$ANVIL_PID"
