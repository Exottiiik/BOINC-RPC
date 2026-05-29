# BOINC - Discord Rich Presence

A lightweight middleware that connects BOINC distributed computing status to Discord Rich Presence.

It displays your current BOINC workload directly in your Discord profile, including :
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

Python dependencies:

```bash
pip install pypresence python-dotenv
````

---

## BOINC Setup

You should refer to :

- [BOINC Official Wiki](https://github.com/BOINC/boinc/wiki/User-manual)
- [BOINC Official Download Page](https://boinc.berkeley.edu/download.php)

### Linux

*Refer to the official BOINC documentation for installation details.*

### Windows

BOINC must be installed and running as a service or background process.

Ensure the RPC file exists:

```
C:\ProgramData\BOINC\gui_rpc_auth.cfg
```

---

## Installation

### 1. Manual installation (recommended for everyone)

This method works regardless of where you place the project.

1. Download the project :

   * Either download the ZIP from GitHub
   * Or copy the files manually into a folder of your choice

For example, you can place it anywhere:

```
Desktop/BOINC-RPC/
Documents/BOINC-RPC/
~/apps/boinc-rpc/
```

What matters is that the folder contains :

```
BOINC-RPC/
├── src/
│   └── boinc_rpc_daemon.py
├── requirements.txt
├── .env.example
```

---

### 2. Install dependencies

Open a terminal inside the project folder *you can type cmd.exe in the path bar in the file explorer or navigate to it manually by using the command `cd`* :

```bash
pip install -r requirements.txt
```

---

## Configuration

This project uses a user-level configuration file.

### Linux

The config file must be created here *using the `.env.example` file that you get from GitHub or the archive you downloaded* :

```text
~/.config/boinc-rpc/.env
````

### Windows

The config file must be created here :

```text
%USERPROFILE%\.config\boinc-rpc\.env
```
*example : `C:\Users\Alice\.config\boinc-rpc\.env`*.

Yes, the same structure is used on both systems for consistency.
*On Windows, `%USERPROFILE%` resolves automatically to `C:\Users\YourName`*

---

### Step-by-step setup

#### 1. Create the config directory

##### Linux

```bash
mkdir -p ~/.config/boinc-rpc
```

##### Windows (PowerShell)

```powershell
mkdir $env:USERPROFILE\.config\boinc-rpc
```

---

#### 2. Create the `.env` file

Copy `.env.example` into the correct location *you need to be in the folder of the project (BOINC-RPC for example) folder before trying to copy* :

##### Linux

```bash
cp .env.example ~/.config/boinc-rpc/.env
```

##### Windows (PowerShell)

```powershell
Copy-Item .env.example "$env:USERPROFILE\.config\boinc-rpc\.env"
```

---

#### 3. Edit configuration

Example `.env`:

```ini
DISCORD_CLIENT_ID=1509951042958266580
BOINC_HOST=127.0.0.1
BOINC_PORT=31416

# Linux:
BOINC_PASSWORD_PATH=/var/lib/boinc/gui_rpc_auth.cfg

# Windows:
# BOINC_PASSWORD_PATH=C:\ProgramData\BOINC\gui_rpc_auth.cfg

UPDATE_INTERVAL=15
DEBUG_MODE=False
```

*an .env.example file is available in the GitHub if you need to customize it...*

---

## Running the project 

### Manually

From the project root :
*project root = the folder containing src/ and requirements.txt*

```bash
python src/boinc_rpc_daemon.py
```

### Windows auto-start 

*I recommend you to take a look [here](https://www.technipages.com/scheduled-task-windows/)*.

### Systemd Service (Linux auto-start)

Create service file :

```bash
mkdir -p ~/.config/systemd/user/
nano ~/.config/systemd/user/boinc-discord.service
```

Service configuration :

```ini
[Unit]
Description=BOINC Discord Rich Presence Middleware
After=network.target

[Service]
Type=simple
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=%h/.local/bin:/usr/bin"
WorkingDirectory=%h/BOINC-RPC
ExecStart=/usr/bin/python3 %h/BOINC-RPC/src/boinc_rpc_daemon.py
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

*The service assumes the project is located in ~/BOINC-RPC. Son make sure that the `WorkingDirectory` and `ExecStart` are correct for your installation.*

Enable service :

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

### BOINC RPC Layer

* TCP connection (31416)
* XML-based protocol
* MD5 authentication

### Python Middleware

* XML parsing
* Task filtering
* State normalization
* Safe fallback handling

### Discord IPC Layer

* pypresence integration
* Rich Presence updates
* Automatic reconnect

---

## Limitations

* BOINC XML structure varies across versions
* Some fields may be missing or reset depending on client state
* Project names derived from URL (not always clean)
* Local machine only (no remote BOINC support)
* Discord rate limits apply to update frequency
* GPU reporting depends on BOINC + driver stack behavior
* Windows support is supposed functional but less extensively tested

---

## Notes

This project was initially developed as a personal middleware between BOINC and Discord.
It prioritizes simplicity and real-time feedback over strict enterprise architecture.

Suitable for:

* personal monitoring
* BOINC learning
* Discord IPC experimentation

And maybe it needs some adjustment to work nicely with your installation.

---

## License

This project is released under the MIT License.

You are free to use, modify, and distribute this software, provided that the original license notice is included.

This project is provided "as is", without warranty of any kind, expressed or implied. The author is not responsible for any issues arising from its use.
