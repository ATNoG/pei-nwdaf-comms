#!/usr/bin/env bash
set -euo pipefail

BASE="http://localhost:9337/api/v1/ledger"
PASS=0; FAIL=0
# Unique suffix per run so re-runs don't hit duplicate-key errors
RUN="smoke-$(date +%s)"

check() {
  local desc="$1" actual="$2" expect="$3"
  if echo "$actual" | grep -q "$expect"; then
    echo "  PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "  FAIL: $desc"
    echo "        expected to contain: $expect"
    echo "        got: $actual"
    FAIL=$((FAIL+1))
  fi
}

echo "==> Checking sidecar health..."
HEALTH=$(curl -sf --max-time 5 "$BASE/../../../actuator/health" 2>/dev/null || echo "DOWN")
check "sidecar is UP" "$HEALTH" "UP"

echo "==> Data-fetch operations..."
POST=$(curl -s --max-time 10 -X POST "$BASE/data-fetch" \
  -H 'Content-Type: application/json' \
  -d "{\"requestId\":\"${RUN}-df\",\"mlflowRunId\":\"${RUN}\",\"modelName\":\"anomaly\",\"modelVersion\":\"1.0\",\"queryDescriptor\":\"{}\",\"dataHash\":\"aabbcc\",\"timeRangeStart\":\"2026-01-01T00:00:00Z\",\"timeRangeEnd\":\"2026-01-02T00:00:00Z\"}")
check "POST data-fetch returns requestId" "$POST" "${RUN}-df"

GET=$(curl -s --max-time 10 "$BASE/data-fetch/${RUN}-df")
check "GET data-fetch by ID" "$GET" "aabbcc"

BY_RUN=$(curl -s --max-time 10 "$BASE/data-fetch/by-run/${RUN}")
check "GET data-fetch by run ID" "$BY_RUN" "${RUN}-df"

NOTFOUND=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE/data-fetch/no-such-id")
check "GET missing data-fetch returns 404" "$NOTFOUND" "404"

echo "==> Inference operations..."
INF=$(curl -s --max-time 10 -X POST "$BASE/inference" \
  -H 'Content-Type: application/json' \
  -d "{\"inferenceId\":\"${RUN}-inf\",\"mlflowRunId\":\"${RUN}\",\"modelName\":\"anomaly\",\"modelVersion\":\"1.0\",\"dataFetchRef\":\"${RUN}-df\",\"inputHash\":\"ddeeff\",\"anomalyScore\":0.91,\"decision\":\"ANOMALY\"}")
check "POST inference returns inferenceId" "$INF" "${RUN}-inf"

GETINF=$(curl -s --max-time 10 "$BASE/inference/${RUN}-inf")
check "GET inference by ID" "$GETINF" "0.91"

echo "==> Provenance..."
PROV=$(curl -s --max-time 10 "$BASE/provenance/${RUN}-inf")
check "GET provenance contains inference" "$PROV" "${RUN}-inf"
check "GET provenance contains linked data-fetch" "$PROV" "${RUN}-df"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && echo "All tests passed." || { echo "Some tests failed."; exit 1; }
