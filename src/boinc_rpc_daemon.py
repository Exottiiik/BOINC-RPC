#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BOINC - Discord Rich Presence (V2 Multi-Host)
A lightweight middleware to display BOINC tasks in Discord.
Supports monitoring multiple BOINC nodes across the network.
"""

import os
import time
import json
import socket
import hashlib
import logging
import platform
import xml.etree.ElementTree as ET

from urllib.parse import urlparse
from pathlib import Path
from pypresence import Presence

# ---------------------------------------------------------------------------
# OS & LOGGING DETECTION
# ---------------------------------------------------------------------------
CURRENT_OS = platform.system()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("BOINCDiscordRPC")

# ---------------------------------------------------------------------------
# CONFIGURATION MANAGEMENT (JSON)
# ---------------------------------------------------------------------------
CONFIG_DIR = Path.home() / ".config" / "boinc-rpc"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_BOINC_PASSWORD = (
    r"C:\ProgramData\BOINC\gui_rpc_auth.cfg"
    if CURRENT_OS == "Windows"
    else "/var/lib/boinc/gui_rpc_auth.cfg"
)

DEFAULT_CONFIG = {
    "discord_client_id": "1509951042958266580",
    "update_interval": 15,
    "debug_mode": False,
    "nodes": [
        {
            "name": "Localhost",
            "host": "127.0.0.1",
            "port": 31416,
            "password_path": DEFAULT_BOINC_PASSWORD,
            "password": ""
        }
    ]
}

def load_config():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Syntax error in config.json: {e}. Using default config to prevent crash.")
        return DEFAULT_CONFIG

CFG = load_config()

if CFG.get("debug_mode", False):
    logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def safe_float(node):
    try:
        return float(node.text) if node is not None and node.text else 0.0
    except (ValueError, TypeError):
        return 0.0

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}"

def shorten(text, max_len=42):
    if not text:
        return "Unknown"
    return text[:max_len] + ("..." if len(text) > max_len else "")

class BoincRPCError(Exception):
    pass

# ---------------------------------------------------------------------------
# BOINC CLIENT (Multi-Host Support)
# ---------------------------------------------------------------------------
class BoincRPCClient:
    def __init__(self, node_id, name, host, port, password_path, raw_password):
        self.node_id = node_id
        self.name = name
        self.host = host
        self.port = port
        self.password_path = password_path
        self.raw_password = raw_password
        self.sock = None
        self.is_connected = False

    def _get_password(self):
        if self.raw_password:
            return self.raw_password
        if self.password_path and os.path.exists(self.password_path):
            try:
                with open(self.password_path, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"[{self.name}] Password read error: {e}")
        return ""

    def _send_request(self, xml_body):
        payload = f"<boinc_gui_rpc_request>\n{xml_body}\n</boinc_gui_rpc_request>\n\003"
        try:
            self.sock.sendall(payload.encode("utf-8"))
        except socket.error as e:
            raise BoincRPCError(f"Socket send failed: {e}")

        data = b""
        while True:
            try:
                chunk = self.sock.recv(4096)
            except socket.timeout:
                raise BoincRPCError("Socket timeout")
            if not chunk:
                raise BoincRPCError("BOINC socket closed")
            data += chunk
            if b"\003" in chunk:
                break
        return data.decode("utf-8", errors="ignore").rstrip("\003").strip()

    def connect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

        password = self._get_password()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

        try:
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            raise BoincRPCError(f"Connection failed: {e}")

        auth1 = ET.fromstring(self._send_request("<auth1/>"))
        nonce_node = auth1.find("nonce")
        if nonce_node is None:
            raise BoincRPCError("Nonce missing")

        hashv = hashlib.md5((nonce_node.text + password).encode()).hexdigest()
        auth2 = ET.fromstring(self._send_request(f"<auth2><nonce_hash>{hashv}</nonce_hash></auth2>"))

        if auth2.find("authorized") is None:
            raise BoincRPCError("Authentication failed")
            
        self.is_connected = True

# ---------------------------------------------------------------------------
# DISCORD DAEMON (Multi-Node)
# ---------------------------------------------------------------------------
class DiscordBoincDaemon:
    def __init__(self):
        self.client_id = CFG.get("discord_client_id")
        if not self.client_id:
            raise RuntimeError("Missing discord_client_id in config.json")

        self.update_interval = int(CFG.get("update_interval", 15))
        self.rpc = Presence(self.client_id)
        self.discord_connected = False
        self.task_index = 0
        
        # Initialisation dynamique des Nœuds depuis le JSON
        self.nodes = []
        for i, n in enumerate(CFG.get("nodes", [])):
            self.nodes.append(BoincRPCClient(
                node_id=f"NODE {i + 1}",
                name=n.get("name", f"Unknown Node {i + 1}"),
                host=n.get("host", "127.0.0.1"),
                port=int(n.get("port", 31416)),
                password_path=n.get("password_path", ""),
                raw_password=n.get("password", "")
            ))

    def maintain_connections(self):
        if not self.discord_connected:
            try:
                self.rpc.connect()
                self.discord_connected = True
                logger.info("Connected to Discord")
            except Exception:
                logger.debug("Discord unavailable")

        for node in self.nodes:
            if not node.is_connected:
                try:
                    node.connect()
                    logger.info(f"Connected to BOINC node: {node.name} ({node.host}) assigned as {node.node_id}")
                except Exception as e:
                    logger.debug(f"Node {node.name} unavailable: {e}")

    def fetch_all_tasks(self):
        all_tasks = []
        for node in self.nodes:
            if not node.is_connected:
                continue
            try:
                xml_str = node._send_request("<get_results><active_only>1</active_only></get_results>")
                if not xml_str or not xml_str.strip():
                    continue
                    
                xml = ET.fromstring(xml_str)
                for result in xml.findall(".//result"):
                    state = result.find(".//active_task_state")
                    if state is None or state.text != "1":
                        continue

                    name_node = result.find("name")
                    task_name = name_node.text if name_node is not None and name_node.text else "Unknown task"

                    project_node = result.find("project_url")
                    project_name = "Unknown project"
                    if project_node is not None and project_node.text:
                        domain = urlparse(project_node.text).netloc or project_node.text
                        project_name = domain[4:] if domain.startswith("www.") else domain

                    active = result.find(".//active_task")
                    frac_node = active.find("fraction_done") if active is not None else result.find("fraction_done")
                    elapsed_node = active.find("elapsed_time") if active is not None else result.find("elapsed_time")

                    all_tasks.append({
                        "node_id": node.node_id,
                        "node_name": node.name,
                        "name": shorten(task_name, 20),
                        "project": shorten(project_name, 25),
                        "progress": safe_float(frac_node) * 100,
                        "elapsed": safe_float(elapsed_node)
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch tasks from {node.name}: {e}")
                node.is_connected = False
        return all_tasks

    def update_rpc(self, tasks):
        if not tasks:
            self.rpc.clear()
            return

        current = tasks[self.task_index % len(tasks)]
        self.task_index += 1
        
        active_nodes = len(set(t['node_id'] for t in tasks))
        count = len(tasks)

        task_str = 'task' if count == 1 else 'tasks'
        node_str = 'node' if active_nodes == 1 else 'nodes'
        
        details = f"Computing {count} {task_str} across {active_nodes} {node_str}."
        state = f"[{current['node_id']}] TASK : {current['name']} FROM {current['project']} = {current['progress']:.1f}%"

        self.rpc.update(
            details=details,
            state=state,
            large_image="boinc_logo",
            start=int(time.time() - current["elapsed"]),
            buttons=[
                {"label": "What's BOINC ?", "url": "https://boinc.berkeley.edu/"},
                {"label": "Add this to Discord !", "url": "https://github.com/Exottiiik/BOINC-RPC"}
            ]
        )

    def run(self):
        if CURRENT_OS == "Windows":
            import ctypes
            import subprocess
            
            current_pid = os.getpid()
            try:
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'BOINC-Discord-RPC.exe', '/FI', f'PID ne {current_pid}', '/T'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000
                )
            except Exception:
                pass

            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "BOINC_Discord_RPC_SingleInstance")
            if ctypes.windll.kernel32.GetLastError() == 183:
                logger.error("Daemon is already running.")
                return

        logger.info(f"BOINC Discord RPC (Multi-Node) started on {CURRENT_OS}")

        while True:
            self.maintain_connections()

            if self.discord_connected:
                try:
                    tasks = self.fetch_all_tasks()
                    self.update_rpc(tasks)
                except Exception as e:
                    logger.warning(f"Discord IPC pipeline failed: {e}")
                    self.discord_connected = False

            time.sleep(self.update_interval)

if __name__ == "__main__":
    try:
        daemon = DiscordBoincDaemon()
        daemon.run()
    except KeyboardInterrupt:
        logger.info("Daemon stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")