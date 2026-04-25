#!/usr/bin/env bash
# start.sh — Idempotent startup for the NWDAF DLT network.
# Run from the dlt/ directory (or anywhere — script locates itself).
#
# Usage:
#   ./start.sh           — start everything (skips phases already done)
#   ./start.sh --rebuild — force rebuild of the tools and sidecar Docker images
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/fabric-network/docker-compose.yaml"
COMPOSE="docker compose -f ${COMPOSE_FILE}"

REBUILD=false
for arg in "$@"; do
  [ "${arg}" = "--rebuild" ] && REBUILD=true
done

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[DLT]${NC} $*"; }
warn() { echo -e "${YELLOW}[DLT]${NC} $*"; }
err()  { echo -e "${RED}[DLT ERROR]${NC} $*" >&2; }

wait_healthy() {
  local container=$1
  local max_wait=${2:-120}
  local elapsed=0
  until [ "$(docker inspect --format '{{.State.Health.Status}}' "${container}" 2>/dev/null)" = "healthy" ]; do
    elapsed=$((elapsed + 5))
    if [ "${elapsed}" -ge "${max_wait}" ]; then
      err "${container} did not become healthy after ${max_wait}s"
      docker logs --tail=30 "${container}" 2>/dev/null || true
      exit 1
    fi
    echo -n "."
    sleep 5
  done
  echo ""
}

# ── Phase 0: Pre-flight ───────────────────────────────────────────────────────
log "Phase 0: Pre-flight checks..."
docker info > /dev/null 2>&1 || { err "Docker daemon is not running."; exit 1; }

if [ "${REBUILD}" = "true" ]; then
  log "  Rebuilding tools, chaincode and sidecar images..."
  ${COMPOSE} --profile tools build tools
  ${COMPOSE} --profile chaincodes build data-fetch-chaincode
  ${COMPOSE} --profile sidecar build fabric-client-sidecar
else
  # Build images only if they don't exist yet
  if ! docker image inspect fabric-network-tools > /dev/null 2>&1 && \
     ! docker image inspect fabric-network_tools > /dev/null 2>&1; then
    log "  Building tools image (first run)..."
    ${COMPOSE} --profile tools build tools
  fi
  if ! docker image inspect fabric-network-data-fetch-chaincode > /dev/null 2>&1 && \
     ! docker image inspect fabric-network_data-fetch-chaincode > /dev/null 2>&1; then
    log "  Building chaincode image (first run)..."
    ${COMPOSE} --profile chaincodes build data-fetch-chaincode
  fi
fi

# ── Phase 1: Crypto material ──────────────────────────────────────────────────
CRYPTO_DIR="${SCRIPT_DIR}/fabric-network/crypto-config"
ARTIFACTS_DIR="${SCRIPT_DIR}/fabric-network/channel-artifacts"

if [ -d "${CRYPTO_DIR}" ] \
   && [ -f "${ARTIFACTS_DIR}/analytics-genesis.block" ] \
   && [ -f "${ARTIFACTS_DIR}/inference-genesis.block" ]; then
  warn "Phase 1: Crypto material already exists — skipping bootstrap."
else
  log "Phase 1: Generating crypto material and genesis blocks..."
  ${COMPOSE} --profile tools run --rm tools bash /workspace/fabric-network/scripts/bootstrap.sh
  log "Phase 1: Done."
fi

# ── Phase 2: Start core network ───────────────────────────────────────────────
log "Phase 2: Starting core network services..."
${COMPOSE} up -d ca.nwdaf.local orderer.nwdaf.local couchdb peer0.nwdaf.local

log "  Waiting for orderer to be healthy..."
wait_healthy "orderer.nwdaf.local" 120

log "  Waiting for peer to be healthy..."
wait_healthy "peer0.nwdaf.local" 120

log "Phase 2: Core network is healthy."

# ── Phase 3: Channel setup ────────────────────────────────────────────────────
# Check if both channels exist on the peer already
PEER_CHANNELS=$(${COMPOSE} --profile tools run --rm --no-TTY tools bash -c \
  'peer channel list 2>/dev/null || echo ""' 2>/dev/null || echo "")

if echo "${PEER_CHANNELS}" | grep -qw "analytics-channel" && \
   echo "${PEER_CHANNELS}" | grep -qw "inference-channel"; then
  warn "Phase 3: Both channels already exist — skipping setup."
else
  log "Phase 3: Setting up channels..."
  ${COMPOSE} --profile tools run --rm tools bash /workspace/fabric-network/scripts/setup-channels.sh
  log "Phase 3: Done."
fi

# ── Phase 4: Chaincode deployment ─────────────────────────────────────────────
check_committed() {
  local channel=$1 name=$2
  ${COMPOSE} --profile tools run --rm --no-TTY tools bash -c \
    "peer lifecycle chaincode querycommitted \
       --channelID ${channel} --name ${name} --output json 2>/dev/null \
     | python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"sequence\",0))' 2>/dev/null \
     || echo 0" 2>/dev/null | tr -d '[:space:]' || echo "0"
}

ANALYTICS_SEQ=$(check_committed "analytics-channel" "data-fetch-chaincode")
INFERENCE_SEQ=$(check_committed "inference-channel"  "inference-chaincode")

if [ "${ANALYTICS_SEQ}" -ge "1" ] && [ "${INFERENCE_SEQ}" -ge "1" ]; then
  warn "Phase 4: Chaincodes already deployed — skipping."
else
  log "Phase 4: Deploying chaincodes (CCAAS — install + approve + commit)..."
  ${COMPOSE} --profile tools run --rm tools bash /workspace/fabric-network/scripts/deploy-chaincode.sh
  log "Phase 4: Done."
fi

# ── Phase 5: Chaincode containers (CCAAS) ────────────────────────────────────
log "Phase 5: Starting chaincode service containers..."
${COMPOSE} --profile chaincodes up -d data-fetch-chaincode inference-chaincode
log "Phase 5: Chaincode containers started."

# ── Phase 6: Sidecar ──────────────────────────────────────────────────────────
log "Phase 6: Starting fabric-client-sidecar..."
${COMPOSE} --profile sidecar up -d fabric-client-sidecar

log "  Waiting for sidecar to be healthy (up to 180s for JVM startup)..."
wait_healthy "fabric-client-sidecar" 180

log "Phase 6: Sidecar is healthy."

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NWDAF DLT Network is UP"
echo ""
echo "  Sidecar REST API : http://localhost:9337/api/v1/ledger"
echo "  CouchDB UI       : http://localhost:5984/_utils  (admin / adminpw)"
echo "  Orderer ops      : http://localhost:9443/healthz"
echo "  Peer ops         : http://localhost:9444/healthz"
echo ""
echo "  Quick smoke test:"
echo "    curl -s http://localhost:9337/api/v1/ledger/data-fetch/no-such-id"
echo ""
echo "  Record a data fetch:"
echo "    curl -s -X POST http://localhost:9337/api/v1/ledger/data-fetch \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"requestId\":\"test-01\",\"mlflowRunId\":\"run-1\",\"modelName\":\"anomaly\",\"modelVersion\":\"1.0\",\"queryDescriptor\":\"{}\",\"dataHash\":\"abc123\",\"cellIds\":\"\",\"timeRangeStart\":\"\",\"timeRangeEnd\":\"\"}'"
echo ""
echo "  Python SDK usage:"
echo "    from dlt_client import AnalyticsChannelClient, InferenceChannelClient"
echo "    analytics = AnalyticsChannelClient('http://localhost:9337')"
echo "    inference = InferenceChannelClient('http://localhost:9337')"
echo ""
echo "  Stop:         ./stop.sh"
echo "  Stop + clean: ./stop.sh --clean"
echo "  Rebuild imgs: ./start.sh --rebuild"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
