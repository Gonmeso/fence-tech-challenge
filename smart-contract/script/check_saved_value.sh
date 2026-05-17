#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  check_saved_value.sh <contract_address> <facility> [rpc_url]

Arguments:
  contract_address  Deployed FacilityCovenantRegistry address.
  facility          Allowed values: educa, payearly, nomia.
                    "nomia" is accepted and mapped to the on-chain facility "nomina".
  rpc_url           Optional RPC URL. Defaults to $RPC_URL or http://127.0.0.1:8545.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage >&2
  exit 1
fi

contract_address="$1"
requested_facility="$2"
rpc_url="${3:-${RPC_URL:-http://127.0.0.1:8545}}"

case "$requested_facility" in
  educa | payearly)
    facility="$requested_facility"
    ;;
  nomia | nomina)
    facility="nomina"
    ;;
  *)
    echo "Unsupported facility: $requested_facility" >&2
    echo "Allowed values: educa, payearly, nomia" >&2
    exit 1
    ;;
esac

echo "Contract: $contract_address"
echo "Requested facility: $requested_facility"
echo "On-chain facility: $facility"
echo "RPC URL: $rpc_url"
echo

echo "reportExists($facility)"
cast call \
  "$contract_address" \
  "reportExists(string)(bool)" \
  "$facility" \
  --rpc-url "$rpc_url"

echo
echo "getFacilityReport($facility)"
cast call \
  "$contract_address" \
  "getFacilityReport(string)((string,uint16,uint8,uint32,uint32,uint32,string[],(string,string[])[],uint64,address,bool))" \
  "$facility" \
  --rpc-url "$rpc_url"
