# BOINC - Discord Rich Presence

A lightweight middleware that connects BOINC distributed computing status to Discord Rich Presence.

It displays your current BOINC workload directly in your Discord profile, including  :
- Number of active tasks
- Task progress
- Task runtime
- Project metadata (optional)

This project acts as a bridge between BOINC’s local RPC interface and Discord’s Rich Presence IPC system.

---

## Features

- Cross-platform support (Linux / Windows)
- Automatic BOINC RPC authentication (MD5 nonce handshake)
- Active task monitoring with rotation display
- Real-time progress and elapsed time tracking
- Automatic reconnection (BOINC / Discord)
- Lightweight and low resource usage
- Fully local (no external API required)

---

## Requirements

- Python 3.8+
- BOINC client running locally
- Discord desktop application (Rich Presence enabled)

Python dependencies :

```bash
pip install pypresence python-dotenv
````

---

## Configuration


Create a .env file in the project directory.

### Linux

```ini
DISCORD_CLIENT_ID=your_discord_application_id
BOINC_HOST=127.0.0.1
BOINC_PORT=31416
BOINC_PASSWORD_PATH=/var/lib/boinc/gui_rpc_auth.cfg
UPDATE_INTERVAL=15
DEBUG_MODE=False
```

### Windows

```ini
DISCORD_CLIENT_ID=your_discord_application_id
BOINC_HOST=127.0.0.1
BOINC_PORT=31416
BOINC_PASSWORD_PATH=C:\ProgramData\BOINC\gui_rpc_auth.cfg
UPDATE_INTERVAL=15
DEBUG_MODE=False
```

---

## BOINC Setup

### Linux

Install BOINC :

```bash
sudo apt install boinc-client
# or
sudo dnf install boinc-client
```

Ensure your user has access to the BOINC RPC interface :

```bash
sudo usermod -aG boinc $USER
```

Then log out and log back in.

---

### Windows

BOINC configuration file location :

```
C:\ProgramData\BOINC\gui_rpc_auth.cfg
```

Make sure :

* BOINC is running in background or as a service
* The GUI RPC interface is enabled

---

## Running manually

```bash
python boinc_rpc_daemon.py
```

---

## Systemd Service (Linux)

Create the service file :

`~/.config/systemd/user/boinc-discord.service`

```ini
[Unit]
Description=BOINC Discord Rich Presence Middleware
After=network.target

[Service]
Type=simple
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=%h/.local/bin:/usr/bin"
EnvironmentFile=%h/.config/boinc-rpc/.env
ExecStart=/usr/bin/python3 %h/.local/bin/boinc_rpc_daemon.py
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

Enable and start :

```bash
systemctl --user daemon-reload
systemctl --user enable --now boinc-discord.service
```

Logs :

```bash
journalctl --user -u boinc-discord.service -f
```

---

## Architecture

The system is composed of three main layers :

### 1. BOINC RPC Layer

* TCP connection on port 31416
* XML-based communication protocol
* MD5 nonce authentication (local only)

### 2. Python Middleware

* XML parsing via ElementTree
* Task filtering and aggregation
* State normalization across BOINC versions
* Reconnection logic for robustness

### 3. Discord IPC Layer

* Managed via `pypresence`
* Updates Discord Rich Presence
* Handles connection drops gracefully

---

## Limitations

This project is functional and stable for everyday use, but some constraints exist due to BOINC and Discord APIs :

* BOINC XML structure is not fully consistent across all client versions.
   Fields like `fraction_done` and `elapsed_time` may appear at different XML depths (`result` or `active_task`). This can occasionally result in missing or reset values (e.g. 0% progress or 0 :00 elapsed time).

* Project metadata is simplified.
   Project names are sometimes derived from `project_url`, which is not always human-readable. A more accurate mapping can be achieved by correlating with `get_state()`.

* Task rotation behavior is intentional.
   The displayed task rotates over time rather than always selecting the most important one. This provides a dynamic “live activity” effect but is not a strict priority scheduler.

* Local-only usage.
   The tool requires a BOINC instance running on the same machine. Remote BOINC instances are not supported.

* Discord update rate limits.
   Extremely frequent updates may be throttled by Discord’s Rich Presence system.

* GPU detection may potentially interfere with task reporting, although this has not been confirmed.
   In some personal tests (notably on AMD setups under Fedora), GPU-related activity was not always consistently reflected in BOINC’s RPC output. 
  However, it is unclear whether this comes from BOINC itself, the driver stack, or the way GPU is detected.

* Windows support is "available" but not fully validated...
   The project has been primarily developed and tested on Linux environments (Fedora-based systems). 
   Windows compatibility is implemented, but has not been extensively tested in real-world usage and may require additional adjustments depending on BOINC installation paths or permissions.

---

## Notes

This project was originally developed as a personal middleware and experimental integration between BOINC and Discord.

It has been tested in real desktop environments (Linux and Windows with BOINC + Discord running locally) and works reliably for continuous usage.

Some design choices prioritize simplicity and responsiveness over strict production-grade architecture, especially in task selection and XML normalization.

This makes it suitable for :

* Personal monitoring dashboards
* Learning BOINC RPC and Discord IPC
* Experimental telemetry middleware projects

### Development notes

Some parts of this project were assisted by **AI-based code generation** tools during development.

The final implementation, testing, and integration were reviewed and adapted manually.

---

## License

This project is released under the MIT License.

You are free to use, modify, and distribute this software, provided that the original license notice is included.

This project is provided "as is", without warranty of any kind, expressed or implied. The author is not responsible for any issues arising from its use.
