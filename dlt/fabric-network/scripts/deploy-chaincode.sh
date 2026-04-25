#!/usr/bin/env bash
# deploy-chaincode.sh — run via:  docker compose run --rm tools bash scripts/deploy-chaincode.sh
# Uses CCAAS (Chaincode as a Service): each chaincode is a gRPC server container.
# fabric-javaenv was removed in Fabric 2.5; Docker-build mode is not supported.
set -euo pipefail

ORDERER_HOST="${ORDERER_HOST:-orderer.nwdaf.local}"
PEER_HOST="${PEER_HOST:-peer0.nwdaf.local}"
ORDERER_PORT="${ORDERER_PORT:-7050}"
PEER_PORT="${PEER_PORT:-7051}"

FABRIC_NET_DIR="/workspace/fabric-network"
CRYPTO_DIR="${FABRIC_NET_DIR}/crypto-config"

export FABRIC_CFG_PATH="/usr/local/fabric/config"
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=NWDAFMSP
export CORE_PEER_ADDRESS="${PEER_HOST}:${PEER_PORT}"
export CORE_PEER_TLS_ROOTCERT_FILE="${CRYPTO_DIR}/peerOrganizations/nwdaf.local/peers/peer0.nwdaf.local/tls/ca.crt"
export CORE_PEER_MSPCONFIGPATH="${CRYPTO_DIR}/peerOrganizations/nwdaf.local/users/Admin@nwdaf.local/msp"

ORDERER_CA="${CRYPTO_DIR}/ordererOrganizations/nwdaf.local/orderers/orderer.nwdaf.local/tls/ca.crt"

ORDERER_FLAGS=(
  -o "${ORDERER_HOST}:${ORDERER_PORT}"
  --ordererTLSHostnameOverride orderer.nwdaf.local
  --tls
  --cafile "${ORDERER_CA}"
)

# ── Package ───────────────────────────────────────────────────────────────────
# CCAAS packages: metadata.json + code.tar.gz (containing connection.json).
# peer lifecycle chaincode package --lang ccaas is not supported in Fabric 2.5.9;
# packages must be built manually. The ccaas_builder detect script looks for
# {"type":"ccaas"} in metadata.json.
echo "==> Packaging chaincodes (CCAAS)..."

make_ccaas_package() {
  local label=$1
  local address=$2
  local output=$3
  local work
  work=$(mktemp -d)
  echo "{\"address\":\"${address}\",\"dial_timeout\":\"10s\",\"tls_required\":false}" \
    > "${work}/connection.json"
  echo "{\"type\":\"ccaas\",\"label\":\"${label}\"}" \
    > "${work}/metadata.json"
  tar czf "${work}/code.tar.gz" -C "${work}" connection.json
  tar czf "${output}" -C "${work}" metadata.json code.tar.gz
  rm -rf "${work}"
}

make_ccaas_package "data-fetch-chaincode_1.0" "data-fetch-chaincode:7052" \
  /tmp/data-fetch-chaincode.tar.gz

make_ccaas_package "inference-chaincode_1.0" "inference-chaincode:7052" \
  /tmp/inference-chaincode.tar.gz

echo "    Packaged."

# ── Install ───────────────────────────────────────────────────────────────────
get_pkg_id() {
  local label=$1
  peer lifecycle chaincode queryinstalled --output json 2>/dev/null \
    | python3 -c "
import sys, json
for cc in json.load(sys.stdin).get('installed_chaincodes', []):
    if cc['label'] == '${label}':
        print(cc['package_id'])
        break
" 2>/dev/null || echo ""
}

PKG_ID_ANALYTICS=$(get_pkg_id "data-fetch-chaincode_1.0")
if [ -n "${PKG_ID_ANALYTICS}" ]; then
  echo "==> data-fetch-chaincode already installed: ${PKG_ID_ANALYTICS}"
else
  echo "==> Installing data-fetch-chaincode..."
  peer lifecycle chaincode install /tmp/data-fetch-chaincode.tar.gz
  PKG_ID_ANALYTICS=$(get_pkg_id "data-fetch-chaincode_1.0")
fi

PKG_ID_INFERENCE=$(get_pkg_id "inference-chaincode_1.0")
if [ -n "${PKG_ID_INFERENCE}" ]; then
  echo "==> inference-chaincode already installed: ${PKG_ID_INFERENCE}"
else
  echo "==> Installing inference-chaincode..."
  peer lifecycle chaincode install /tmp/inference-chaincode.tar.gz
  PKG_ID_INFERENCE=$(get_pkg_id "inference-chaincode_1.0")
fi

if [ -z "${PKG_ID_ANALYTICS}" ] || [ -z "${PKG_ID_INFERENCE}" ]; then
  echo "ERROR: could not retrieve package IDs after install"
  exit 1
fi
echo "    data-fetch-chaincode: ${PKG_ID_ANALYTICS}"
echo "    inference-chaincode:  ${PKG_ID_INFERENCE}"

# ── Deploy function ───────────────────────────────────────────────────────────
deploy_on_channel() {
  local CC_NAME=$1
  local CHANNEL=$2
  local PKG_ID=$3
  echo ""
  echo "==> ${CC_NAME} → ${CHANNEL}"

  COMMITTED=$(peer lifecycle chaincode querycommitted \
    --channelID "${CHANNEL}" --name "${CC_NAME}" --output json 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('sequence',0))" 2>/dev/null \
    || echo "0")

  if [ "${COMMITTED}" -ge "1" ]; then
    echo "    Already committed at sequence ${COMMITTED}, skipping."
    return 0
  fi

  echo "    approving..."
  peer lifecycle chaincode approveformyorg \
    "${ORDERER_FLAGS[@]}" \
    --channelID "${CHANNEL}" \
    --name "${CC_NAME}" \
    --version 1.0 \
    --sequence 1 \
    --package-id "${PKG_ID}"

  echo "    checking readiness..."
  peer lifecycle chaincode checkcommitreadiness \
    --channelID "${CHANNEL}" \
    --name "${CC_NAME}" \
    --version 1.0 \
    --sequence 1 \
    --output json

  echo "    committing..."
  peer lifecycle chaincode commit \
    "${ORDERER_FLAGS[@]}" \
    --channelID "${CHANNEL}" \
    --name "${CC_NAME}" \
    --version 1.0 \
    --sequence 1

  echo "    verifying..."
  peer lifecycle chaincode querycommitted \
    --channelID "${CHANNEL}" \
    --name "${CC_NAME}" \
    --output json

  echo "    done."
}

deploy_on_channel "data-fetch-chaincode" "analytics-channel" "${PKG_ID_ANALYTICS}"
deploy_on_channel "inference-chaincode"  "inference-channel"  "${PKG_ID_INFERENCE}"

# Write package IDs to .env so docker-compose injects CORE_CHAINCODE_ID_NAME
# into each chaincode container (required by fabric-chaincode-shim even in CCAAS mode).
cat > "${FABRIC_NET_DIR}/.env" <<EOF
DATA_FETCH_CC_ID=${PKG_ID_ANALYTICS}
INFERENCE_CC_ID=${PKG_ID_INFERENCE}
EOF
echo "==> Wrote chaincode IDs to ${FABRIC_NET_DIR}/.env"

echo ""
echo "==> Deployment complete."
echo "    data-fetch-chaincode → analytics-channel  (${PKG_ID_ANALYTICS})"
echo "    inference-chaincode  → inference-channel   (${PKG_ID_INFERENCE})"
echo ""
echo "    Start chaincode containers and sidecar:"
echo "    docker compose --profile chaincodes up -d"
echo "    docker compose --profile sidecar up -d fabric-client-sidecar"
