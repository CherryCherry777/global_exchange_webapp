#!/usr/bin/env bash
# setup_global_exchange.sh (updated 2025-10)
# Installs everything for the Global Exchange project: dependencies, repos, Docker, Redis, Celery, Django.
# Tested on Ubuntu 22.04, 24.04, 25.04 (Xia). Handles unsupported Docker codenames automatically.

set -euo pipefail

############################################
# Defaults
############################################
BASE_DIR_DEFAULT="$HOME/proyectos"
WEBAPP_REPO="https://github.com/CherryCherry777/global_exchange_webapp.git"
WEBAPP_BRANCH="desarrollo"
WEBAPP_DIR_NAME="global_exchange_webapp"

SQLPROXY_REPO="https://gitlab.com/ggonza732/sql-proxy01.git"
SQLPROXY_DIR_NAME="sql-proxy01"

DB_NAME_DEFAULT="global_exchange"
DB_USER_DEFAULT="postgres"
DB_PASS_DEFAULT="postgres"
DB_HOST_DEFAULT="localhost"
DB_PORT_DEFAULT="5432"

MAIL_HOST_DEFAULT="sandbox.smtp.mailtrap.io"
MAIL_PORT_DEFAULT="2525"
MAIL_USE_TLS_DEFAULT="True"
MAIL_USER_DEFAULT="proveido_por_mailtrap"
MAIL_PASS_DEFAULT="proveido_por_mailtrap"

STRIPE_PK_DEFAULT="pk_test_01829398"
STRIPE_SK_DEFAULT="sk_test_01928392"

# Flags
ENV_FILE=""
BASE_DIR="$BASE_DIR_DEFAULT"
ONLY_PHASE=""
FROM_PHASE=""
TO_PHASE=""
NON_INTERACTIVE="false"
ASSUME_YES="false"
RUNSERVER_BG="false"
CELERY_BG="false"

############################################
# Helpers
############################################
log() { printf "\n\033[1;36m[INFO]\033[0m %s\n" "$*"; }
warn() { printf "\n\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err() { printf "\n\033[1;31m[ERR ]\033[0m %s\n" "$*"; }
die() { err "$*"; exit 1; }

ask() {
  local prompt="$1" default="${2:-}"
  local answer
  if [[ "$NON_INTERACTIVE" == "true" ]]; then
    [[ -n "$default" ]] && echo "$default" && return 0
    die "Non-interactive mode requires default for: $prompt"
  fi
  if [[ -n "$default" ]]; then
    read -r -p "$prompt [$default]: " answer || true
    echo "${answer:-$default}"
  else
    read -r -p "$prompt: " answer || true
    echo "$answer"
  fi
}

confirm() {
  local msg="$1" default_yes="${2:-false}"
  local def_prompt="y/N"
  [[ "$default_yes" == "true" ]] && def_prompt="Y/n"
  if [[ "$ASSUME_YES" == "true" ]]; then
    [[ "$default_yes" == "true" ]] && return 0 || return 1
  fi
  read -r -p "$msg ($def_prompt): " resp || true
  resp="${resp:-$([[ "$default_yes" == "true" ]] && echo y || echo n)}"
  [[ "$resp" =~ ^[Yy]$ ]]
}

need_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }

is_local_host() {
  case "${DB_HOST:-localhost}" in
    ""|"localhost"|"127.0.0.1"|"::1") return 0 ;;
    *) return 1 ;;
  esac
}


ensure_local_postgres_db() {
  log "Verificando/creando usuario y base de datos en PostgreSQL local…"
  sudo systemctl enable postgresql >/dev/null 2>&1 || true
  sudo systemctl start postgresql

  # Escapa comillas simples en la contraseña
  local esc_pwd="${DB_PASSWORD//\'/\'''}"

  # Crear o actualizar rol
  sudo -u postgres psql -v ON_ERROR_STOP=1 -q <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE "${DB_USER}" LOGIN PASSWORD '${esc_pwd}';
  ELSE
    ALTER ROLE "${DB_USER}" LOGIN PASSWORD '${esc_pwd}';
  END IF;
END
\$\$;
SQL

  # Crear base de datos si no existe
  if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
    log "Base de datos '${DB_NAME}' no encontrada — creando…"
    sudo -u postgres psql -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\" TEMPLATE template0 ENCODING 'UTF8';"
  else
    log "Base de datos '${DB_NAME}' ya existe — no se crea."
  fi
}

phase_should_run() {
  local n="$1"
  if [[ -n "$ONLY_PHASE" ]]; then [[ "$ONLY_PHASE" == "$n" ]] && return 0 || return 1; fi
  if [[ -n "$FROM_PHASE" || -n "$TO_PHASE" ]]; then
    local from="${FROM_PHASE:-0}" to="${TO_PHASE:-999}"
    (( n >= from && n <= to )) && return 0 || return 1
  fi
  return 0
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --env-file) ENV_FILE="$2"; shift 2;;
      --base-dir) BASE_DIR="$2"; shift 2;;
      --only) ONLY_PHASE="$2"; shift 2;;
      --from) FROM_PHASE="$2"; shift 2;;
      --to) TO_PHASE="$2"; shift 2;;
      --non-interactive) NON_INTERACTIVE="true"; shift;;
      --yes|-y) ASSUME_YES="true"; shift;;
      --runserver-bg) RUNSERVER_BG="true"; shift;;
      --celery-bg) CELERY_BG="true"; shift;;
      --help|-h)
        cat <<EOF
Usage: bash $0 [options]

Options:
  --env-file <path>     Use an existing .env file.
  --base-dir <dir>      Working directory base (default: $BASE_DIR_DEFAULT)
  --only <n>            Run only phase n (0-9)
  --from <n>            Run from phase n
  --to <n>              Run until phase n
  --non-interactive     No prompts; requires defaults
  --yes, -y             Assume "yes" for confirmations
  --runserver-bg        Run Django in background
  --celery-bg           Run Celery worker/beat in background
EOF
        exit 0;;
      *) die "Unknown option: $1";;
    esac
  done
}

############################################
# Globals
############################################
WEBAPP_DIR=""
SQLPROXY_DIR=""
ENV_PATH=""
DJANGO_VENV_PATH=""
PYTHON_BIN="python3"
PIP_BIN="pip3"

############################################
# Phase 0 — Setup
############################################
phase_0() {
  log "Phase 0 — Checking system and prerequisites"
  need_cmd sudo; need_cmd bash
  sudo apt update -y
  sudo apt install -y git curl wget gnupg lsb-release build-essential python3 python3-venv python3-pip

  BASE_DIR="${BASE_DIR:-$BASE_DIR_DEFAULT}"
  mkdir -p "$BASE_DIR"
  WEBAPP_DIR="$BASE_DIR/$WEBAPP_DIR_NAME"
  SQLPROXY_DIR="$BASE_DIR/$SQLPROXY_DIR_NAME"
}

############################################
# Phase 1 — Clone webapp, venv, requirements, .env, PostgreSQL
############################################
phase_1() {
  log "Phase 1 — WebApp setup"
  if [[ ! -d "$WEBAPP_DIR/.git" ]]; then git clone "$WEBAPP_REPO" "$WEBAPP_DIR"; fi
  cd "$WEBAPP_DIR"
  git fetch --all
  git checkout "$WEBAPP_BRANCH"

  DJANGO_VENV_PATH="$WEBAPP_DIR/venv"
  [[ -d "$DJANGO_VENV_PATH" ]] || python3 -m venv "$DJANGO_VENV_PATH"
  # shellcheck source=/dev/null
  source "$DJANGO_VENV_PATH/bin/activate"
  PYTHON_BIN="python"; PIP_BIN="pip"
  $PIP_BIN install --upgrade pip wheel
  [[ -f requirements.txt ]] && $PIP_BIN install -r requirements.txt || warn "No requirements.txt"

  # Copy or create .env
  if [[ -n "$ENV_FILE" ]]; then
    ENV_PATH="$WEBAPP_DIR/.env"
    cp -f "$ENV_FILE" "$ENV_PATH" || die "Cannot copy $ENV_FILE"
  else
    ENV_PATH="$WEBAPP_DIR/.env"
    DB_NAME="$(ask 'DB_NAME' "$DB_NAME_DEFAULT")"
    DB_USER="$(ask 'DB_USER' "$DB_USER_DEFAULT")"
    DB_PASSWORD="$(ask 'DB_PASSWORD' "$DB_PASS_DEFAULT")"
    DB_HOST="$(ask 'DB_HOST' "$DB_HOST_DEFAULT")"
    DB_PORT="$(ask 'DB_PORT' "$DB_PORT_DEFAULT")"
    EMAIL_HOST="$(ask 'EMAIL_HOST' "$MAIL_HOST_DEFAULT")"
    EMAIL_HOST_USER="$(ask 'EMAIL_HOST_USER' "$MAIL_USER_DEFAULT")"
    EMAIL_HOST_PASSWORD="$(ask 'EMAIL_HOST_PASSWORD' "$MAIL_PASS_DEFAULT")"
    STRIPE_PUBLIC_KEY="$(ask 'STRIPE_PUBLIC_KEY' "$STRIPE_PK_DEFAULT")"
    STRIPE_SECRET_KEY="$(ask 'STRIPE_SECRET_KEY' "$STRIPE_SK_DEFAULT")"
    cat >"$ENV_PATH" <<EOF
EMAIL_HOST=$EMAIL_HOST
EMAIL_HOST_USER=$EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD
EMAIL_PORT=$MAIL_PORT_DEFAULT
EMAIL_USE_TLS=$MAIL_USE_TLS_DEFAULT
STRIPE_PUBLIC_KEY=$STRIPE_PUBLIC_KEY
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
EOF
  fi

  # Fix CRLF if present
  if file "$ENV_PATH" | grep -q CRLF; then
    log "Fixing CRLF line endings in .env..."
    sed -i 's/\r$//' "$ENV_PATH"
  fi

  # Install PostgreSQL
  log "Installing PostgreSQL..."
  sudo apt install -y postgresql postgresql-contrib
  set -a; source "$ENV_PATH"; set +a

  if is_local_host; then
    ensure_local_postgres_db
  else
    warn "DB_HOST='${DB_HOST}' no es local. Omitiendo creación de usuario/DB local."
    warn "Asegúrate de que la base '${DB_NAME}' exista y sea accesible en ${DB_HOST}:${DB_PORT}."
  fi
}

############################################
# Phase 2 — Docker install (auto codename fix)
############################################
phase_2() {
  log "Phase 2 — Installing Docker"
  sudo apt remove -y docker docker-engine docker.io containerd runc || true
  sudo apt install -y ca-certificates curl gnupg lsb-release

  sudo mkdir -p /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  fi

  CODENAME="$(lsb_release -cs 2>/dev/null || echo noble)"
  case "$CODENAME" in
    xia|mantic|minotaur|lunar|oracular|devel|rolling)
      echo "[WARN] Ubuntu codename '$CODENAME' not supported by Docker; using 'noble'."
      CODENAME="noble"
      ;;
  esac

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${CODENAME} stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  # --- Install Docker ---
  log "Installing Docker packages..."
  if ! sudo apt update -y; then
    warn "APT update failed once — retrying with 'noble' codename."
    CODENAME="noble"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${CODENAME} stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update -y
  fi

  if ! sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin; then
    warn "Docker install failed for '$CODENAME'. Forcing codename to 'noble' and retrying."
    CODENAME="noble"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${CODENAME} stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update -y
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  fi

  sudo docker run --rm hello-world || true

  if ! groups "$USER" | grep -q docker; then
    sudo usermod -aG docker "$USER"
    warn "Added $USER to docker group — please re-login or run: newgrp docker"
  fi
}

############################################
# Remaining phases are unchanged in logic
############################################
phase_3() { log "Phase 3 — Verifying Docker"; docker --version || true; docker compose version || true; }
phase_4() { log "Phase 4 — Cloning SQL-Proxy"; [[ -d "$SQLPROXY_DIR/.git" ]] || git clone "$SQLPROXY_REPO" "$SQLPROXY_DIR"; }
phase_5() { log "Phase 5 — Setting permissions"; cd "$SQLPROXY_DIR"; for p in ./volumes/nginx/logs ./volumes/web-sched/logs ./volumes/web/logs ./volumes/web/kude; do mkdir -p "$p"; chmod a+rw "$p"; done; }
phase_6() { log "Phase 6 — Building and starting containers"; cd "$SQLPROXY_DIR"; docker compose -f docker-compose.test.yml build; docker compose -f docker-compose.test.yml up -d; docker ps; }
phase_7_0() { log "Phase 7.0 - make migrations in sql-proxy"; cd "$WEBAPP_DIR"; source "$DJANGO_VENV_PATH/bin/activate" ; $PYTHON_BIN manage.py makemigrations; $PYTHON_BIN manage.py migrate;}
phase_7() { log "Phase 7.1 — Running client/setup_and_run.sh"; cd "$SQLPROXY_DIR/client"; [[ -x setup_and_run.sh ]] && bash setup_and_run.sh || warn "setup_and_run.sh not found"; }
phase_8() {
  log "Phase 8 — Installing Redis and Celery"
  sudo apt install -y redis-server
  sudo systemctl enable redis-server
  sudo systemctl start redis-server
  cd "$WEBAPP_DIR"
  source "$DJANGO_VENV_PATH/bin/activate"
  $PIP_BIN install redis
  if [[ "$CELERY_BG" == "true" ]]; then
    mkdir -p logs/celery
    nohup celery -A web_project worker -l info > logs/celery/worker.log 2>&1 &
    nohup celery -A web_project beat -l info > logs/celery/beat.log 2>&1 &
    log "Celery running in background; logs in logs/celery/"
  else
    log "Run manually: celery -A web_project worker -l info & celery -A web_project beat -l info &"
  fi
}
phase_9() {
  log "Phase 9 — Django migrations and runserver"
  cd "$WEBAPP_DIR"
  source "$DJANGO_VENV_PATH/bin/activate"
  $PYTHON_BIN manage.py makemigrations
  $PYTHON_BIN manage.py migrate
  if [[ "$RUNSERVER_BG" == "true" ]]; then
    nohup $PYTHON_BIN manage.py runserver > logs/django_runserver.log 2>&1 &
    log "Django running (background) → http://127.0.0.1:8000"
  else
    (sleep 2; command -v xdg-open && xdg-open "http://127.0.0.1:8000" || true) &
    $PYTHON_BIN manage.py runserver
  fi
}

############################################
# Main
############################################
main() {
  parse_args "$@"
  exec > >(tee -a "$HOME/setup_global_exchange.log") 2>&1
  phase_should_run 0 && phase_0
  phase_should_run 1 && phase_1
  phase_should_run 2 && phase_2
  phase_should_run 3 && phase_3
  phase_should_run 4 && phase_4
  phase_should_run 5 && phase_5
  phase_should_run 6 && phase_6
  phase_should_run 7 && phase_7
  phase_should_run 8 && phase_8
  phase_should_run 9 && phase_9
  log "✅ All phases completed. Logs → $HOME/setup_global_exchange.log"
}

main "$@"
