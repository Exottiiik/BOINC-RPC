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

# 2. Wizard for configuration (json file)
CONFIG_DIR="$HOME/.config/boinc-rpc"
CONFIG_FILE="$CONFIG_DIR/config.json"

mkdir -p "$CONFIG_DIR"

echo ""
echo "[Info] Depending on your Linux distribution or if you use Flatpak/Snap,"
echo "       the BOINC data directory might be located elsewhere."
echo "       Standard path is usually: /var/lib/boinc/gui_rpc_auth.cfg"
echo -n "Path to gui_rpc_auth.cfg [/var/lib/boinc/gui_rpc_auth.cfg]: "
read BOINC_PATH
BOINC_PATH=${BOINC_PATH:-/var/lib/boinc/gui_rpc_auth.cfg}

# JSON Generation
cat <<EOF > "$CONFIG_FILE"
{
  "discord_client_id": "1509951042958266580",
  "update_interval": 15,
  "debug_mode": false,
  "nodes": [
    {
      "name": "Local Node",
      "host": "127.0.0.1",
      "port": 31416,
      "password_path": "$BOINC_PATH",
      "password": ""
    }
  ]
}
EOF

echo "[OK] Configuration saved in $CONFIG_FILE"

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