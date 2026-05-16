#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ANVIL_HOST="${ANVIL_HOST:-127.0.0.1}"
ANVIL_PORT="${ANVIL_PORT:-8545}"
ANVIL_CHAIN_ID="${ANVIL_CHAIN_ID:-31337}"
ANVIL_LOG="${ANVIL_LOG:-/tmp/fence-anvil.log}"
RPC_URL="http://${ANVIL_HOST}:${ANVIL_PORT}"
PRIVATE_KEY="${PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}"

cleanup() {
  if [[ -n "${ANVIL_PID:-}" ]]; then
    kill "$ANVIL_PID" >/dev/null 2>&1 || true
  fi
}

wait_for_anvil() {
  for _ in {1..60}; do
    if curl -fsS \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
      "$RPC_URL" >/dev/null; then
      return 0
    fi
    sleep 0.5
  done

  echo "Anvil did not become ready at $RPC_URL" >&2
  return 1
}

read_contract_address() {
  local broadcast_file="$1"
  python3 - "$broadcast_file" <<'PY'
import json
import sys
from pathlib import Path

broadcast = json.loads(Path(sys.argv[1]).read_text())
for transaction in broadcast.get("transactions", []):
    contract_address = transaction.get("contractAddress")
    if contract_address:
        print(contract_address)
        break
else:
    raise SystemExit("No contract address found in broadcast file")
PY
}

trap cleanup EXIT INT TERM

anvil --host "$ANVIL_HOST" --port "$ANVIL_PORT" --chain-id "$ANVIL_CHAIN_ID" >"$ANVIL_LOG" 2>&1 &
ANVIL_PID="$!"

wait_for_anvil

(
  cd "$REPO_ROOT/smart-contract"
  PRIVATE_KEY="$PRIVATE_KEY" forge script \
    script/Deploy.s.sol:DeployFacilityCovenantRegistry \
    --rpc-url "$RPC_URL" \
    --broadcast
)

BROADCAST_FILE="$REPO_ROOT/smart-contract/broadcast/Deploy.s.sol/${ANVIL_CHAIN_ID}/run-latest.json"
CONTRACT_ADDRESS="$(read_contract_address "$BROADCAST_FILE")"

export FENCE_WEB3_RPC_URL="$RPC_URL"
export FENCE_WEB3_CHAIN_ID="$ANVIL_CHAIN_ID"
export FENCE_COVENANT_REGISTRY_ADDRESS="$CONTRACT_ADDRESS"
export FENCE_COVENANT_REGISTRY_PRIVATE_KEY="$PRIVATE_KEY"

echo "Anvil: $RPC_URL"
echo "Registry: $CONTRACT_ADDRESS"

"$REPO_ROOT/scripts/run_local_api.sh" "$@"
