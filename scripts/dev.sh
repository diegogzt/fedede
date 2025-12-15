#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[dev.sh] Falta comando requerido: $1" >&2
    exit 1
  }
}

is_port_free() {
  local port="$1"
  ! lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

find_free_port() {
  local start="$1"
  local port="$start"
  while ! is_port_free "$port"; do
    port=$((port + 1))
  done
  echo "$port"
}

wait_for_http() {
  local url="$1"
  local tries="${2:-40}"
  local sleep_s="${3:-0.25}"

  for _ in $(seq 1 "$tries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
  done

  echo "[dev.sh] Timeout esperando: $url" >&2
  return 1
}

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

need_cmd python3
need_cmd node
need_cmd npm
need_cmd curl
need_cmd lsof

FRONTEND_PORT="$(find_free_port "${PORT_START:-3000}")"
# Backend en puerto distinto, pero accesible desde el MISMO puerto del frontend via /api
BACKEND_PORT="$(find_free_port "${BACKEND_PORT_START:-8000}")"
if [[ "$BACKEND_PORT" == "$FRONTEND_PORT" ]]; then
  BACKEND_PORT="$(find_free_port "$((BACKEND_PORT + 1))")"
fi

echo "[dev.sh] Usando FRONTEND_PORT=$FRONTEND_PORT"
echo "[dev.sh] Usando BACKEND_PORT=$BACKEND_PORT (proxied por /api)"

# Backend deps (venv local)
VENV_DIR="$ROOT_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[dev.sh] Creando venv en $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[dev.sh] Instalando dependencias backend (requirements.txt)"
pip -q install --upgrade pip >/dev/null
pip -q install -r "$ROOT_DIR/requirements.txt"

# Frontend deps
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "[dev.sh] Instalando dependencias frontend (npm install)"
  (cd "$FRONTEND_DIR" && npm install)
fi

# Start backend
export PYTHONPATH="$BACKEND_DIR"
export BACKEND_PORT
export BACKEND_URL="http://127.0.0.1:$BACKEND_PORT"

echo "[dev.sh] Arrancando backend..."
( cd "$ROOT_DIR" && python3 -m uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" ) &
BACKEND_PID=$!

wait_for_http "http://127.0.0.1:$BACKEND_PORT/" 60 0.25

# Start frontend on chosen port, with backend env for rewrites
export PORT="$FRONTEND_PORT"

echo "[dev.sh] Arrancando frontend..."
( cd "$FRONTEND_DIR" && BACKEND_URL="$BACKEND_URL" BACKEND_PORT="$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" ) &
FRONTEND_PID=$!

wait_for_http "http://127.0.0.1:$FRONTEND_PORT/" 120 0.25
wait_for_http "http://127.0.0.1:$FRONTEND_PORT/api/" 120 0.25

echo ""
echo "[dev.sh] OK"
echo "- App:      http://127.0.0.1:$FRONTEND_PORT"
echo "- API(/api): http://127.0.0.1:$FRONTEND_PORT/api/"
echo ""

# Keep running
wait
