#!/usr/bin/env bash
# tg-details-bot installer — self-hosted VM, polling mode via systemd.
# Idempotent: safe to re-run (updates code, deps, and restarts the service).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/arkhivar/tg-details-bot/main/deploy/install.sh | sudo TELEGRAM_BOT_TOKEN="123:abc" bash
#   — or from a cloned repo:
#   sudo TELEGRAM_BOT_TOKEN="123:abc" bash deploy/install.sh
#
# Env overrides: INSTALL_DIR (default /opt/tg-details-bot), SERVICE_USER (default tgbot),
#                REPO_URL, TELEGRAM_BOT_TOKEN (required for the service to start).
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/tg-details-bot}"
SERVICE_USER="${SERVICE_USER:-tgbot}"
REPO_URL="${REPO_URL:-https://github.com/arkhivar/tg-details-bot.git}"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run as root (sudo bash deploy/install.sh)"

# --- 1. Python 3.10+ (aiogram 3.x works on any modern Python, including
#         Ubuntu 24.04's native Python 3.12) -----------------------------------
command -v python3 >/dev/null 2>&1 || {
    log "python3 not found, trying to install it"
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq
        apt-get install -y -qq python3 || die "Could not install python3 via apt. Install Python 3.10+ manually, then re-run."
    else
        die "python3 (>= 3.10) is required but not installed, and this script only auto-installs on apt-based systems. Install Python 3.10+ manually, then re-run."
    fi
}
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || \
    die "Python >= 3.10 is required (found: $(python3 --version 2>&1)). Install a newer Python, then re-run."
python3 -c 'import ensurepip' >/dev/null 2>&1 || {
    log "installing python3-venv"
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq
        apt-get install -y -qq python3-venv python3-full || die "python3-venv missing and could not be installed"
    else
        die "python3 venv module missing. Install it (e.g. apt install python3-venv python3-full), then re-run."
    fi
}
log "using $(python3 --version)"

# --- 2. Code -----------------------------------------------------------------
if [ -d "$INSTALL_DIR/.git" ]; then
    log "updating existing install in $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only
elif [ -f "$(dirname "$0")/../main.py" ]; then
    log "running from a cloned repo — using it as the source"
    [ "$INSTALL_DIR" = "$(cd "$(dirname "$0")/.." && pwd)" ] || {
        mkdir -p "$INSTALL_DIR"
        cp -a "$(cd "$(dirname "$0")/.." && pwd)/." "$INSTALL_DIR/"
    }
else
    log "cloning $REPO_URL into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# --- 3. Virtualenv + dependencies --------------------------------------------
[ -x venv/bin/python ] || { log "creating venv"; python3 -m venv venv; }
log "installing dependencies"
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

# --- 4. Configuration ---------------------------------------------------------
if [ ! -f .env ]; then
    cp .env.example .env
    log "created .env from template"
fi
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}|" .env
fi
chmod 600 .env

TOKEN_SET=1
grep -qE '^TELEGRAM_BOT_TOKEN=[0-9]+:.+' .env || TOKEN_SET=0

# --- 5. Service user ------------------------------------------------------------
id -u "$SERVICE_USER" >/dev/null 2>&1 || {
    log "creating service user '$SERVICE_USER'"
    useradd -r -s /usr/sbin/nologin "$SERVICE_USER"
}
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# --- 6. systemd ------------------------------------------------------------------
log "installing systemd unit"
cp deploy/tg-details-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tg-details-bot >/dev/null

if [ "$TOKEN_SET" -eq 1 ]; then
    log "starting service"
    systemctl restart tg-details-bot
    sleep 2
    systemctl --no-pager --full status tg-details-bot | head -n 12 || true
    log "DONE. Follow logs with:  journalctl -u tg-details-bot -f"
else
    log "DONE, but TELEGRAM_BOT_TOKEN is not set."
    echo "    1. Get a token from @BotFather"
    echo "    2. Put it in $INSTALL_DIR/.env"
    echo "    3. systemctl start tg-details-bot"
fi
