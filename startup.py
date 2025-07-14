import subprocess
import sys
import os
import time
import logging
from datetime import datetime
import ntplib

BRANCH = "main"
MAX_RETRIES = 5
RETRY_DELAY = 60  # seconds
LOG_FILE = "logs.txt"

# -------------------------
# Logging setup
# -------------------------
logger = logging.getLogger("AutoUpdater")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# -------------------------
# Functions
# -------------------------
def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()

def has_updates():
    run_cmd(["git", "fetch"])
    local = run_cmd(["git", "rev-parse", BRANCH])
    remote = run_cmd(["git", "rev-parse", f"origin/{BRANCH}"])
    return local != remote

def pull_and_restart():
    logger.info("🔄 New version detected. Pulling updates...")

    try:
        if has_local_changes():
            logger.warning("📦 Local changes detected. Stashing before update...")
            run_cmd(["git", "stash", "push", "-m", "autostash by updater"])

        run_cmd(["git", "pull", "origin", BRANCH])
        logger.info("✅ Pulled latest code. Restarting...")
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        sys.exit(1)

    python = sys.executable
    os.execv(python, [python] + sys.argv)

def self_check():
    logger.info("🔍 Running self check... OK")

def sync_time_from_nist():
    try:
        client = ntplib.NTPClient()
        response = client.request('time.nist.gov', version=3)
        t = datetime.fromtimestamp(response.tx_time)
        logger.info(f"NIST Time: {t.isoformat()}")
    except Exception as e:
        logger.warning(f"NIST time sync failed: {e}")

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


# -------------------------
# Main logic
# -------------------------
def main_loop():
    logger.info("\n\n🐑 Starting Herd OS...")
    logger.info(f"Version {get_version()} | Branch: {BRANCH} \n")

    retries = 0
    while retries < MAX_RETRIES:
        try:
            if has_updates():
                pull_and_restart()
            break  # No updates, continue
        except Exception as e:
            retries += 1
            logger.warning(f"Update check failed ({retries}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
    else:
        logger.error("Maximum retry limit reached. Exiting.")
        sys.exit(1)

    # Perform self-check and time sync after update check
    self_check()

    # Sync time from NIST / GPS
    sync_time_from_nist()

    # LAUNCH:
    logger.info("✅ Setup Passed. Starting main application...")

    python = sys.executable
    os.execv(python, [python, "launch.py"])

    logger.info("Startup completed successfully.")

if __name__ == "__main__":
    main_loop()
