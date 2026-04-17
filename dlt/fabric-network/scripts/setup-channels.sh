#!/usr/bin/env bash
# setup-channels.sh — run via:  docker compose run --rm tools bash scripts/setup-channels.sh
# Expects the network (orderer + peer) to already be running.
set -euo pipefail

ORDERER_HOST="${ORDERER_HOST:-orderer.nwdaf.local}"
PEER_HOST="${PEER_HOST:-peer0.nwdaf.local}"
ORDERER_ADMIN_PORT="${ORDERER_ADMIN_PORT:-7053}"
PEER_PORT="${PEER_PORT:-7051}"

FABRIC_NET_DIR="/workspace/fabric-network"
CRYPTO_DIR="${FABRIC_NET_DIR}/crypto-config"
ARTIFACTS_DIR="${FABRIC_NET_DIR}/channel-artifacts"

# peer CLI needs core.yaml — point at the bundled Fabric sample config
export FABRIC_CFG_PATH="/usr/local/fabric/config"

# peer env — used for all peer commands
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=NWDAFMSP
export CORE_PEER_ADDRESS="${PEER_HOST}:${PEER_PORT}"
export CORE_PEER_TLS_ROOTCERT_FILE="${CRYPTO_DIR}/peerOrganizations/nwdaf.local/peers/peer0.nwdaf.local/tls/ca.crt"
export CORE_PEER_MSPCONFIGPATH="${CRYPTO_DIR}/peerOrganizations/nwdaf.local/users/Admin@nwdaf.local/msp"

ORDERER_CA="${CRYPTO_DIR}/ordererOrganizations/nwdaf.local/orderers/orderer.nwdaf.local/tls/ca.crt"
ORDERER_CERT="${CRYPTO_DIR}/ordererOrganizations/nwdaf.local/orderers/orderer.nwdaf.local/tls/server.crt"
ORDERER_KEY="${CRYPTO_DIR}/ordererOrganizations/nwdaf.local/orderers/orderer.nwdaf.local/tls/server.key"

OSNADMIN_FLAGS=(
  -o "${ORDERER_HOST}:${ORDERER_ADMIN_PORT}"
  --ca-file   "${ORDERER_CA}"
  --client-cert "${ORDERER_CERT}"
  --client-key  "${ORDERER_KEY}"
)

echo "==> Checking cert SANs (debug)..."
openssl x509 -in "${ORDERER_CERT}" -text -noout \
  | grep -A1 "Subject Alternative Name" || true

echo "==> Waiting for orderer to be ready..."
WAIT_COUNT=0; MAX_WAIT=60
until osnadmin channel list "${OSNADMIN_FLAGS[@]}" &>/dev/null; do
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [ "${WAIT_COUNT}" -ge "${MAX_WAIT}" ]; then
    echo "ERROR: orderer did not become ready after $((MAX_WAIT * 2))s. Aborting."
    exit 1
  fi
  echo "    orderer not ready yet (${WAIT_COUNT}/${MAX_WAIT}), retrying in 2s..."
  sleep 2
done

# Check which channels already exist on the orderer
ORDERER_CHANNELS=$(osnadmin channel list "${OSNADMIN_FLAGS[@]}" --output json 2>/dev/null \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('channels', []):
    print(c['name'])
" 2>/dev/null || true)

if echo "${ORDERER_CHANNELS}" | grep -qw "analytics-channel"; then
  echo "==> analytics-channel already on orderer, skipping."
else
  echo "==> Creating analytics-channel..."
  osnadmin channel join \
    --channelID analytics-channel \
    --config-block "${ARTIFACTS_DIR}/analytics-genesis.block" \
    "${OSNADMIN_FLAGS[@]}"
fi

if echo "${ORDERER_CHANNELS}" | grep -qw "inference-channel"; then
  echo "==> inference-channel already on orderer, skipping."
else
  echo "==> Creating inference-channel..."
  osnadmin channel join \
    --channelID inference-channel \
    --config-block "${ARTIFACTS_DIR}/inference-genesis.block" \
    "${OSNADMIN_FLAGS[@]}"
fi

echo "==> Waiting for peer to be ready..."
WAIT_COUNT=0; MAX_WAIT=60
until peer channel list &>/dev/null; do
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [ "${WAIT_COUNT}" -ge "${MAX_WAIT}" ]; then
    echo "ERROR: peer did not become ready after $((MAX_WAIT * 2))s. Aborting."
    exit 1
  fi
  echo "    peer not ready yet (${WAIT_COUNT}/${MAX_WAIT}), retrying in 2s..."
  sleep 2
done

# Check which channels the peer has already joined
PEER_CHANNELS=$(peer channel list 2>/dev/null || true)

if echo "${PEER_CHANNELS}" | grep -qw "analytics-channel"; then
  echo "==> Peer already joined analytics-channel, skipping."
else
  echo "==> Joining peer to analytics-channel..."
  peer channel join -b "${ARTIFACTS_DIR}/analytics-genesis.block"
fi

if echo "${PEER_CHANNELS}" | grep -qw "inference-channel"; then
  echo "==> Peer already joined inference-channel, skipping."
else
  echo "==> Joining peer to inference-channel..."
  peer channel join -b "${ARTIFACTS_DIR}/inference-genesis.block"
fi

echo ""
echo "==> Channel setup complete."
echo "    Run: docker compose run --rm tools bash scripts/deploy-chaincode.sh"
