#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BOINC - Discord Rich Presence
Supposed to work with Linux and Windows environnements as well.

But maybe, I didn't make all the needed tests... What a shame !
(you can either dm me or make a PR ?)
"""

import os
import time
import socket
import hashlib
import logging
import platform
import xml.etree.ElementTree as ET

from pathlib import Path
from dotenv import load_dotenv
from pypresence import Presence

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

BASE_ENV = Path.home() / ".config" / "boinc-rpc" / ".env"
load_dotenv(BASE_ENV)

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

logger = logging.getLogger("BOINCDiscordRPC")

# ---------------------------------------------------------------------------
# OS DETECTION
# ---------------------------------------------------------------------------

CURRENT_OS = platform.system()

DEFAULT_BOINC_PASSWORD = (
    r"C:\ProgramData\BOINC\gui_rpc_auth.cfg"
    if CURRENT_OS == "Windows"
    else "/var/lib/boinc/gui_rpc_auth.cfg"
)

# ---------------------------------------------------------------------------
# CONFIG RESOLUTION
# ---------------------------------------------------------------------------

BOINC_PASSWORD_PATH = os.getenv("BOINC_PASSWORD_PATH", DEFAULT_BOINC_PASSWORD)
BOINC_HOST = os.getenv("BOINC_HOST", "127.0.0.1")
BOINC_PORT = int(os.getenv("BOINC_PORT", "31416"))
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "15"))

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

# ---------------------------------------------------------------------------
# EXCEPTION
# ---------------------------------------------------------------------------

class BoincRPCError(Exception):
    pass

# ---------------------------------------------------------------------------
# BOINC CLIENT
# ---------------------------------------------------------------------------

class BoincRPCClient:

    def __init__(self, host, port, password_path):
        self.host = host
        self.port = port
        self.password_path = password_path
        self.sock = None
        self.password = ""

    def _read_password(self):

        if not os.path.exists(self.password_path):
            logger.warning(f"BOINC password file not found: {self.password_path}")
            return ""

        try:
            with open(self.password_path, "r") as f:
                return f.read().strip()

        except PermissionError:
            logger.error("Permission denied reading BOINC password file.")
            return ""

        except Exception as e:
            logger.error(f"Password read error: {e}")
            return ""

    def _send_request(self, xml_body):

        payload = (
            f"<boinc_gui_rpc_request>\n"
            f"{xml_body}\n"
            f"</boinc_gui_rpc_request>\n\003"
        )

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

        self.password = self._read_password()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

        try:
            self.sock.connect((self.host, self.port))

        except socket.error as e:
            raise BoincRPCError(f"BOINC connection failed: {e}")

        # AUTH STEP 1
        auth1 = ET.fromstring(self._send_request("<auth1/>"))

        nonce_node = auth1.find("nonce")

        if nonce_node is None:
            raise BoincRPCError("BOINC nonce missing")

        nonce = nonce_node.text

        # AUTH STEP 2
        hashv = hashlib.md5(
            (nonce + self.password).encode()
        ).hexdigest()

        auth2_xml = (
            f"<auth2>"
            f"<nonce_hash>{hashv}</nonce_hash>"
            f"</auth2>"
        )

        auth2 = ET.fromstring(self._send_request(auth2_xml))

        if auth2.find("authorized") is None:
            raise BoincRPCError("BOINC authentication failed")

    def get_active_tasks(self):

        xml = self._send_request(
            "<get_results><active_only>1</active_only></get_results>"
        )

        if not xml or not xml.strip():
            return ET.Element("results")

        try:
            return ET.fromstring(xml)

        except ET.ParseError as e:
            logger.warning(f"Invalid BOINC XML received: {e}")
            return ET.Element("results")

# ---------------------------------------------------------------------------
# DISCORD DAEMON
# ---------------------------------------------------------------------------

class DiscordBoincDaemon:

    def __init__(self):

        self.client_id = os.getenv("DISCORD_CLIENT_ID")

        if not self.client_id:
            raise RuntimeError("Missing DISCORD_CLIENT_ID")

        self.boinc_host = os.getenv("BOINC_HOST", "127.0.0.1")

        self.boinc_port = int(
            os.getenv("BOINC_PORT", 31416)
        )

        self.boinc_password = os.getenv(
            "BOINC_PASSWORD_PATH",
            DEFAULT_BOINC_PASSWORD
        )

        self.update_interval = int(
            os.getenv("UPDATE_INTERVAL", 15)
        )

        self.boinc = BoincRPCClient(
            self.boinc_host,
            self.boinc_port,
            self.boinc_password
        )

        self.rpc = Presence(self.client_id)

        self.boinc_connected = False
        self.discord_connected = False

        self.task_index = 0

    # -----------------------------------------------------------------------

    def maintain_connections(self):

        if not self.boinc_connected:

            try:
                self.boinc.connect()
                self.boinc_connected = True
                logger.info("Connected to BOINC")

            except Exception as e:
                logger.debug(f"BOINC unavailable: {e}")

        if not self.discord_connected:

            try:
                self.rpc.connect()
                self.discord_connected = True
                logger.info("Connected to Discord")

            except Exception:
                logger.debug("Discord unavailable")

    # -----------------------------------------------------------------------

    def fetch_tasks(self):

        xml = self.boinc.get_active_tasks()

        tasks = []

        for result in xml.findall(".//result"):

            state = result.find(".//active_task_state")

            if state is None or state.text != "1":
                continue

            # TASK NAME
            name_node = result.find("name")

            task_name = (
                name_node.text
                if name_node is not None and name_node.text
                else "Unknown task"
            )

            # PROJECT
            project_node = result.find("project_url")

            project_name = "unknown project"

            if project_node is not None and project_node.text:
                project_name = project_node.text.split("//")[-1]

            # ACTIVE TASK
            active = result.find(".//active_task")

            if active is not None:

                frac_node = active.find("fraction_done")
                elapsed_node = active.find("elapsed_time")

            else:

                frac_node = result.find("fraction_done")
                elapsed_node = result.find("elapsed_time")

            progress = safe_float(frac_node) * 100
            elapsed = safe_float(elapsed_node)

            tasks.append({
                "name": shorten(task_name),
                "project": shorten(project_name, 28),
                "progress": progress,
                "elapsed": elapsed
            })

        return tasks

    # -----------------------------------------------------------------------

    def update_rpc(self, tasks):

        if not tasks:
            self.rpc.clear()
            return

        current = tasks[self.task_index % len(tasks)]
        self.task_index += 1

        count = len(tasks)

        details = f"Computing for {count} BOINC tasks"

        state = (
            f"Task : {current['name']} "
            f"from {current['project']} "
            f"= {current['progress']:.1f}%"
        )

        hover = (
            f"Elapsed : {format_time(current['elapsed'])}"
        )

        self.rpc.update(
            details=details,
            state=state,
            large_image="boinc_logo",
            large_text=hover,
            small_image="windows_logo" if CURRENT_OS == "Windows" else "fedora_logo",
            small_text=CURRENT_OS,
            start=int(time.time() - current["elapsed"])
        )

    # -----------------------------------------------------------------------

    def run(self):

        logger.info(f"BOINC Discord RPC started on {CURRENT_OS}")

        while True:

            self.maintain_connections()

            if self.boinc_connected and self.discord_connected:

                try:
                    tasks = self.fetch_tasks()
                    self.update_rpc(tasks)

                except Exception as e:
                    logger.warning(f"Telemetry cycle failed: {e}")
                    self.boinc_connected = False

            time.sleep(self.update_interval)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    try:
        daemon = DiscordBoincDaemon()
        daemon.run()

    except KeyboardInterrupt:
        logger.info("Daemon stopped")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
