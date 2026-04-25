#!/usr/bin/env bash
# bootstrap.sh — run via:  docker compose run --rm tools bash scripts/bootstrap.sh
# Everything executes inside the tools container; nothing needed on the host
# except Docker itself.
set -euo pipefail

ORDERER_HOST="${ORDERER_HOST:-orderer.nwdaf.local}"
PEER_HOST="${PEER_HOST:-peer0.nwdaf.local}"
ORDERER_ADMIN_PORT="${ORDERER_ADMIN_PORT:-7053}"
PEER_PORT="${PEER_PORT:-7051}"

# Inside the container, workspace is mounted at /workspace/fabric-network
FABRIC_NET_DIR="/workspace/fabric-network"
CRYPTO_DIR="${FABRIC_NET_DIR}/crypto-config"
ARTIFACTS_DIR="${FABRIC_NET_DIR}/channel-artifacts"

# configtxgen/cryptogen read their config from this path
export FABRIC_CFG_PATH="${FABRIC_NET_DIR}"

echo "==> Cleaning previous state..."
rm -rf "${CRYPTO_DIR}" "${ARTIFACTS_DIR}"

echo "==> Generating crypto material..."
cryptogen generate \
  --config="${FABRIC_NET_DIR}/crypto-config.yaml" \
  --output="${CRYPTO_DIR}"

echo "==> Generating channel genesis blocks..."
mkdir -p "${ARTIFACTS_DIR}"

configtxgen \
  -profile AnalyticsChannel \
  -outputBlock "${ARTIFACTS_DIR}/analytics-genesis.block" \
  -channelID analytics-channel

configtxgen \
  -profile InferenceChannel \
  -outputBlock "${ARTIFACTS_DIR}/inference-genesis.block" \
  -channelID inference-channel

echo "==> Crypto and genesis blocks written. Starting network..."
# The tools container can't run docker compose itself, so we signal the host
# via a sentinel file. The host wrapper script reads this and starts the network.
# (Alternatively, run bootstrap in two phases — see README.)
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  Crypto material and genesis blocks are ready."
echo "  Now start the network from your host:"
echo ""
echo "    docker compose up -d ca.nwdaf.local orderer.nwdaf.local couchdb peer0.nwdaf.local"
echo ""
echo "  Then run the channel setup:"
echo ""
echo "    docker compose run --rm tools bash scripts/setup-channels.sh"
echo "────────────────────────────────────────────────────────────"
