#!/usr/bin/env bash
# Installation script for BOINC Discord RPC (Linux)

echo "=========================================="
echo " BOINC Discord RPC Installation"
echo "=========================================="

# 1. System dependencies check
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python3 is not installed."
    exit 1
fi

# 2. Command-line "Wizard" (.env creation)
CONFIG_DIR="$HOME/.config/boinc-rpc"
ENV_FILE="$CONFIG_DIR/.env"

mkdir -p "$CONFIG_DIR"

echo ""
echo "[Info] Depending on your Linux distribution or if you use Flatpak/Snap,"
echo "       the BOINC data directory might be located elsewhere."
echo "       Standard path is usually: /var/lib/boinc/gui_rpc_auth.cfg"
echo -n "Path to gui_rpc_auth.cfg [/var/lib/boinc/gui_rpc_auth.cfg]: "
read BOINC_PATH
BOINC_PATH=${BOINC_PATH:-/var/lib/boinc/gui_rpc_auth.cfg}

echo "DISCORD_CLIENT_ID=1509951042958266580" > "$ENV_FILE"
echo "BOINC_HOST=127.0.0.1" >> "$ENV_FILE"
echo "BOINC_PORT=31416" >> "$ENV_FILE"
echo "UPDATE_INTERVAL=15" >> "$ENV_FILE"
echo "DEBUG_MODE=False" >> "$ENV_FILE"
echo "BOINC_PASSWORD_PATH=$BOINC_PATH" >> "$ENV_FILE"

echo "[OK] Configuration saved in $ENV_FILE"

# 3. Local virtual environment creation
echo "[Info] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
echo "[OK] Dependencies installed."

# 4. Systemd service installation
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

# Adapt ExecStart path to use the newly created venv
sed "s|ExecStart=.*|ExecStart=$PWD/venv/bin/python3 $PWD/src/boinc_rpc_daemon.py|g" systemd/boinc-discord.service > "$SERVICE_DIR/boinc-discord.service"
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$PWD|g" "$SERVICE_DIR/boinc-discord.service"

systemctl --user daemon-reload
systemctl --user enable --now boinc-discord.service

echo "=========================================="
echo "[Success] BOINC Discord RPC is installed and running in the background!"
echo "To view logs: journalctl --user -u boinc-discord.service -f"
echo "=========================================="