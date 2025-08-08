import subprocess
import sys
import os
import time
import logging
from datetime import datetime
import ntplib
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
import hashlib
import json
import uuid

BRANCH = "main"
MAX_RETRIES = 5
RETRY_DELAY = 60  # seconds
LOG_FILE = "logs.txt"
VENV = "myvenv"

def in_venv():
    return sys.prefix != sys.base_prefix

# -------------------------
# Rich Logging setup
# -------------------------
console = Console()

# Script identifier for common header
SCRIPT_NAME = "STARTUP"

def pastel_color_from_name(name):
    # Hash the name to get a deterministic value
    h = hashlib.md5(name.encode()).hexdigest()
    # Use first 6 hex digits for RGB
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    # Blend with white for pastel effect
    r = (r + 255) // 2
    g = (g + 255) // 2
    b = (b + 255) // 2
    return f"#{r:02x}{g:02x}{b:02x}"

SCRIPT_COLOR = pastel_color_from_name(SCRIPT_NAME)

# Setup rich logging with both file and console handlers
logger = logging.getLogger("AutoUpdater")
logger.setLevel(logging.DEBUG)

# File handler with standard formatting for log file
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(file_formatter)

# Rich console handler with script indicator
class RichHandlerWithScript(RichHandler):
    def format(self, record):
        # Get the original message without Rich's default formatting
        message = record.getMessage()
        
        # Format timestamp as MM/DD/YY HH:MM:SS
        timestamp = datetime.fromtimestamp(record.created).strftime("%m/%d/%y %H:%M:%S")
        
        # Format: [timestamp] SCRIPT_NAME LEVEL    message
        level_name = record.levelname
        formatted = f"[{timestamp}] [bold {SCRIPT_COLOR}]{SCRIPT_NAME}[/bold {SCRIPT_COLOR}] {level_name:<8} {message}"
        
        return formatted

rich_handler = RichHandlerWithScript(
    console=console,
    show_time=False,  # We're handling time ourselves
    show_level=False,  # We're handling level ourselves
    show_path=False,
    rich_tracebacks=True,
    markup=True
)
rich_handler.setFormatter(logging.Formatter("%(message)s"))

logger.addHandler(file_handler)
logger.addHandler(rich_handler)

# -------------------------
# Functions
# -------------------------
def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()

def has_updates():
    need_update = False
    run_cmd(["git", "fetch"])
    local = run_cmd(["git", "rev-parse", BRANCH])
    remote = run_cmd(["git", "rev-parse", f"origin/{BRANCH}"])
    if local != remote:
        need_update = True

    # Check submodules for updates
    # Fetch submodule remotes
    run_cmd(["git", "submodule", "update", "--remote", "--init", "--recursive"])
    # Check if any submodule is not up to date
    sub_status = run_cmd(["git", "submodule", "status", "--recursive"])
    for line in sub_status.splitlines():
        if line.startswith('+') or line.startswith('-'):
            need_update = True
    return need_update

def pull_and_restart():
    logger.info("[bold yellow]🔄 New version detected. Pulling updates (including submodules)...[/bold yellow]")

    try:
        if has_local_changes():
            logger.warning("[yellow]📦 Local changes detected. Stashing before update...[/yellow]")
            run_cmd(["git", "stash", "push", "-m", "autostash by updater"])

        run_cmd(["git", "pull", "origin", BRANCH])
        logger.info("[bold green]✅ Pulled latest code.[/bold green]")

        # Update submodules
        logger.info("[bold yellow]🔄 Checking submodules for updates...[/bold yellow]")
        sub_status = run_cmd(["git", "submodule", "status", "--recursive"])
        for line in sub_status.splitlines():
            status_char = line[0]
            sub_info = line[1:].strip()
            if status_char == '+':
                logger.info(f"[yellow]Submodule ahead of recorded commit: {sub_info}[/yellow]")
            elif status_char == '-':
                logger.info(f"[yellow]Submodule not initialized: {sub_info}[/yellow]")
            elif status_char == 'U':
                logger.info(f"[yellow]Submodule has merge conflicts: {sub_info}[/yellow]")
            elif status_char == ' ':
                logger.info(f"[green]Submodule up to date: {sub_info}[/green]")
            else:
                logger.info(f"[magenta]Submodule status {status_char}: {sub_info}[/magenta]")

        logger.info("[bold yellow]🔄 Updating submodules...[/bold yellow]")
        run_cmd(["git", "submodule", "update", "--init", "--recursive"])
        # git pull origin heads/main
        logger.info("[bold green]✅ Submodules updated.[/bold green]")

        logger.info("[bold green]Restarting...[/bold green]")
    except Exception as e:
        logger.error(f"[bold red]❌ Update or submodule update failed: {e}[/bold red]")
        sys.exit(1)

    python = sys.executable
    os.execv(python, [python] + sys.argv)

def self_check():
    logger.info("[bold blue]🔍 Running self check...[/bold blue] [green]OK[/green]")

def sync_time_from_nist():
    try:
        client = ntplib.NTPClient()
        before = time.time()
        response = client.request('time.nist.gov', version=3)
        nist_time = response.tx_time
        after = time.time()
        delta_before = nist_time - before
        delta_after = nist_time - after
        t = datetime.fromtimestamp(nist_time)
        logger.info(f"[cyan]NIST Time: {t.isoformat()}[/cyan]")
        logger.info(f"[magenta]Time delta before sync: {delta_before:.3f} seconds[/magenta]")
        logger.info(f"[magenta]Time delta after sync: {delta_after:.3f} seconds[/magenta]")
    
        if delta_before > 0.1:
            logger.warning("You may want to add that HW update for time sync to your startup script.. tsk tsk tsk")
    
    except Exception as e:
        logger.warning(f"[yellow]NIST time sync failed: {e}[/yellow]")

def get_version():
    try:
        # Use `git describe` if you use tags, otherwise fallback to short hash
        return run_cmd(["git", "describe", "--always", "--dirty"])
    except Exception as e:
        logger.warning(f"Could not determine version: {e}")
        return "unknown"

def has_local_changes():
    status = run_cmd(["git", "status", "--porcelain"])
    return bool(status.strip())

def startup_device_id():
    device_id = None
    if os.path.exists(CFG_FILE):
        try:
            with open(CFG_FILE, "r") as f:
                data = json.load(f)
                device_id = data.get("device_id")
        except Exception as e:
            logger.warning(f"[yellow]Failed to read {CFG_FILE}: {e}[/yellow]")

    if not device_id or device_id is None or device_id == "":
        device_id = str(uuid.uuid4())
        try:
            with open(CFG_FILE, "w") as f:
                json.dump({"device_id": device_id}, f)
            logger.info(f"[green]Generated new device_id: {device_id}[/green]")
        except Exception as e:
            logger.error(f"[red]Failed to write {CFG_FILE}: {e}[/red]")
            sys.exit(1)
    else:
        logger.info(f"[cyan]Device ID: {device_id}[/cyan]")

# -------------------------
# Globals logic
# -------------------------
CFG_FILE = "./device.cfg"

# -------------------------
# Main logic
# -------------------------
def main_loop():
    logger.info("\n\n[bold blue]🐑 Starting Herd OS...[/bold blue]")
    logger.info(f"[green]Version {get_version()}[/green] | [cyan]Branch: {BRANCH}[/cyan] \n")

    startup_device_id()

    retries = 0
    while retries < MAX_RETRIES:
        try:
            if has_updates():
                pull_and_restart()
            break  # No updates, continue
        except Exception as e:
            retries += 1
            logger.warning(f"[yellow]Update check failed ({retries}/{MAX_RETRIES}): {e}[/yellow]")
            time.sleep(RETRY_DELAY)
    else:
        logger.error("[red]Maximum retry limit reached. Exiting.[/red]")
        sys.exit(1)

    # Perform self-check and time sync after update check
    self_check()

    # Sync time from NIST / GPS
    sync_time_from_nist()

    # LAUNCH:
    logger.info("[bold green]✅ Setup Passed. Starting main application...[/bold green]")

    python = sys.executable
    os.execv(python, [python, "launch.py"])

    logger.info("[bold green]Startup completed successfully.[/bold green]")

if __name__ == "__main__":
    main_loop()
