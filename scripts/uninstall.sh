#!/usr/bin/env bash
# Uninstallation script for BOINC Discord RPC (Linux)

echo "[Info] Stopping BOINC Discord RPC service..."
systemctl --user stop boinc-discord.service 2>/dev/null
systemctl --user disable boinc-discord.service 2>/dev/null

echo "[Info] Removing systemd service file..."
rm -f "$HOME/.config/systemd/user/boinc-discord.service"
systemctl --user daemon-reload

echo "[Info] Removing installation directory... (if it exists and was created by the installer, if not, you may need to change the path in the script to match your installation)"
rm -rf "$HOME/BOINC-RPC"

echo "[Success] BOINC Discord RPC has been uninstalled."
echo "Note: Configuration files in ~/.config/boinc-rpc were kept."