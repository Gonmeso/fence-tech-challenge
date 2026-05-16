#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_URL="${API_URL:-http://127.0.0.1:8000}"

post_facility() {
  local facility="$1"
  local file="$2"

  echo
  echo "POST /api/v1/covenants/calculate [$facility]"
  curl -sS \
    -X POST "$API_URL/api/v1/covenants/calculate" \
    -H "Content-Type: application/json" \
    -H "X-Fence-Facility-Type: $facility" \
    --data-binary "@$file" | jq .

  echo
  echo "GET /api/v1/covenants/result [$facility]"
  curl -sS \
    "$API_URL/api/v1/covenants/result" \
    -H "X-Fence-Facility-Type: $facility" | jq .
  echo
}

curl -sS "$API_URL/api/v1/health"
echo

post_facility "educa" "$REPO_ROOT/data/facility_a_educa_isa.json" 
post_facility "payearly" "$REPO_ROOT/data/facility_b_payearly_ewa.json"
post_facility "nomina" "$REPO_ROOT/data/facility_c_nomina.json"
