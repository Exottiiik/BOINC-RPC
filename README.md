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
- Active task monitoring with rotation display (5 tasks running = 5 taks rotation ~15s each one)
- Real-time progress and elapsed time tracking
- Automatic reconnection (BOINC / Discord *with some latency yeah*)
- Lightweight and low resource usage
- Fully local (no external API required)

---

## Requirements
*this may vary based on your operating system and the used installation method so, don't worry about this right now and skip to [Installation](#installation) !*

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

Ensure the RPC file exists *if you change it, take note of the path* :

```
C:\ProgramData\BOINC\gui_rpc_auth.cfg
```

---

## Installation

### Windows (easy install)

The easiest way to use this tool on Windows is to use the standalone installer. **You do not need to install Python, since it is provided by the installer**.

1. Go to the **[Releases](https://github.com/Exottiiik/BOINC-RPC/releases)** tab on the right side of this GitHub page.
2. Download the latest `BOINC-RPC-Windows-Installer.exe`.
3. Run the installer and follow the setup wizard.
4. *Note: Windows SmartScreen or your Antivirus might flag the installer because it is brand new and not digitally signed by a paid corporate certificate. This is a false positive common with open-source software. Click "More info" -> "Run anyway". On hardened configurations (not default), some errors may occur since specific permissions are needed.*

The installer will automatically set up the embedded environment, configure the BOINC paths, and create a silent Scheduled Task so the RPC starts automatically when you log into Windows.

### Linux (automated bash script)

For Linux users, an interactive bash script is provided to automate the creation of the Python virtual environment and the setup of the `systemd` background service.

**Prerequisites:**
1. **Python `venv`:** ensure you have the virtual environment package installed. On Debian/Ubuntu systems, run `sudo apt install python3-venv` before executing the script.
2. **Systemd :** the auto-start functionality strictly relies on `systemd` running in user mode. Do not run the installation script as `root` (do not use `sudo`), as the Rich Presence IPC socket needs to communicate with your local user's Discord instance.
3. **Flatpak/Snap Users :** the script defaults to the standard package manager path for BOINC (`/var/lib/boinc/gui_rpc_auth.cfg`). If you installed BOINC via Flatpak or Snap, you will need to manually locate this file inside your containerized application folder and provide the custom path when the script prompts you.

**Run the installer:**

Go to the **[Releases](https://github.com/Exottiiik/BOINC-RPC/releases)** tab, download the Linux archive, extract it, and run the script:

```bash
# Download the latest release or use wget (you may need to replace v1.0.0 with the current version)
wget [https://github.com/Exottiiik/BOINC-RPC/releases/download/v1.0.0/BOINC-RPC-Linux-v1.0.0.tar.gz](https://github.com/Exottiiik/BOINC-RPC/releases/download/v1.0.0/BOINC-RPC-Linux-v1.0.0.tar.gz)
# Once downloaded manually or got via wget
tar -xzvf BOINC-RPC-Linux-v1.0.0.tar.gz
cd BOINC-RPC-Linux
chmod +x install.sh
./install.sh

```

*NOTE : you may need to adapt these lines with your own paths and environment...*

---

## Uninstallation

### Windows
1. Open **Windows Settings** > **Apps** > **Installed Apps**.
2. Search for **BOINC Discord RPC**.
3. Click **Uninstall**. 
The uninstaller will automatically stop the daemon, remove the background task, and clean up all files, including the embedded Python environment.

### Linux
If you used the automated script, run the following commands to stop the service and remove the installation folder *or use the provided script* :

```bash
systemctl --user stop boinc-discord.service
systemctl --user disable boinc-discord.service
rm -rf ~/.config/systemd/user/boinc-discord.service
rm -rf ~/BOINC-RPC
# Optionally remove the config files:
rm -rf ~/.config/boinc-rpc
```

---

## Manual Installation / Development

If you prefer to run the script from source manually, follow these steps :

### 1. Install requirements

Requires Python 3.8+.

```bash
pip install -r requirements.txt
```

### 2. Configuration

Create a user-level `.env` file from the example provided:

**Linux:**

```bash
mkdir -p ~/.config/boinc-rpc
cp .env.example ~/.config/boinc-rpc/.env
```

**Windows (PowerShell):**

```powershell
mkdir $env:USERPROFILE\.config\boinc-rpc
Copy-Item .env.example "$env:USERPROFILE\.config\boinc-rpc\.env"
```

Edit the `.env` file to match your `gui_rpc_auth.cfg` path.

### 3. Run

```bash
python src/boinc_rpc_daemon.py
```

*Note : you need to be in the right folder, depending of you installation path, etc.*

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

## Discord Application

This project uses a Discord Application to display Rich Presence information.

You can customize the appearance (name, images, and assets) by creating your own application on the Discord Developer Portal:

https://discord.com/developers/applications

Once created, replace the default `DISCORD_CLIENT_ID` in your `.env` file with your own Application ID.

This allows you to:
- Change the application name shown in Discord
- Customize Rich Presence assets (images, icons, etc.)
- Personalize the displayed activity layout

You can also modify the source code if you want to adjust what is displayed (task details, progress format, rotation behavior, etc.).

---

## Limitations

* BOINC XML structure varies across versions
* Some fields may be missing or reset depending on client state
* Project names derived from URL (not always clean but did the best)
* Local machine only (no remote BOINC support)
* Discord rate limits apply to update frequency
* GPU reporting depends on BOINC + driver stack behavior *Fedora issue with AMD GPU*
* Windows support is supposed functional but less extensively tested
* Alternative Discord clients (like Vesktop) can cause issues with the RPC *most probably related to Flatpak installation and permissions*.

---

## Notes

This project was initially developed as a personal middleware between BOINC and Discord.
It prioritizes simplicity and real-time feedback over strict enterprise architecture.

Suitable for :

* personal monitoring
* BOINC learning
* Discord IPC experimentation

And maybe it needs some adjustment to work nicely with your installation but in most case, it should work fine.

---

## License

This project is released under the MIT License.

You are free to use, modify, and distribute this software, provided that the original license notice is included.

This project is provided "as is", without warranty of any kind, expressed or implied. The author is not responsible for any issues arising from its use.