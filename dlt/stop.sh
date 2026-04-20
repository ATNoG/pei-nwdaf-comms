#!/usr/bin/env bash
# stop.sh — Stop the NWDAF DLT network.
#
# Usage:
#   ./stop.sh           — stop containers, keep volumes and crypto-config
#   ./stop.sh --clean   — stop containers AND remove volumes, crypto-config,
#                         channel-artifacts, and the built chaincode jar
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="docker compose -f ${SCRIPT_DIR}/fabric-network/docker-compose.yaml"

CLEAN=false
for arg in "$@"; do
  [ "${arg}" = "--clean" ] && CLEAN=true
done

echo "[DLT] Stopping all services..."
${COMPOSE} --profile sidecar --profile chaincodes --profile tools down

if [ "${CLEAN}" = "true" ]; then
  echo "[DLT] Removing named volumes..."
  ${COMPOSE} down -v 2>/dev/null || true

  echo "[DLT] Removing crypto material..."
  sudo rm -rf "${SCRIPT_DIR}/fabric-network/crypto-config"

  echo "[DLT] Removing channel artifacts..."
  sudo rm -rf "${SCRIPT_DIR}/fabric-network/channel-artifacts"

  echo "[DLT] Removing built chaincode jar..."
  rm -f "${SCRIPT_DIR}/chaincode/build/libs/nwdaf-chaincode.jar"

  echo "[DLT] Clean complete. Next ./start.sh will re-bootstrap from scratch."
else
  echo "[DLT] Stopped. Volumes and crypto-config preserved."
  echo "[DLT] Run './stop.sh --clean' to also remove all persistent data."
fi
