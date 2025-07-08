from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
import threading
import time
import queue
import sys

import zenoh

message_queue = queue.Queue()
devices = {}  # device_id: {"ttl": int, "online": bool, "name": str, "ip": str}
console = Console()

TTL_SECONDS = 10

def listener(sample):
    try:
        msg = bytes(sample.payload).decode("utf-8").strip()
        parts = msg.split(",")
        if len(parts) != 4:
            return
        timestamp, device_id, name, ip = parts

        devices[device_id] = {
            "ttl": TTL_SECONDS,
            "online": True,
            "name": name.strip(),
            "ip": ip.strip()
        }

        message_queue.put(("update", dict(devices)))
    except Exception as e:
        console.print(f"[red]Error parsing IFF message:[/red] {e}")

def ttl_monitor():
    while True:
        time.sleep(1)
        updated = False
        for device_id in list(devices):
            devices[device_id]["ttl"] -= 1
            if devices[device_id]["ttl"] <= 0:
                if devices[device_id]["online"]:
                    devices[device_id]["online"] = False
                    updated = True
                devices[device_id]["ttl"] = 0  # keep from going negative
        if updated:
            message_queue.put(("update", dict(devices)))

def start_iff_listener():
    config = zenoh.Config()
    session = zenoh.open(config)
    session.declare_subscriber("global/IFF", listener)
    while True:
        time.sleep(1)

def render_table(device_status):
    table = Table(title="Connected Devices")
    table.add_column("Device ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("IP", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("TTL", style="white", justify="right")

    for device_id, info in device_status.items():
        status = "🟢 Online" if info["online"] else "🔴 Offline"
        ttl = str(info["ttl"])
        table.add_row(device_id, info["name"], info["ip"], status, ttl)
    return table

def command_interface():
    config = zenoh.Config()
    session = zenoh.open(config)
    pub = session.declare_publisher("global/COMMAND")

    while True:
        command = Prompt.ask("[bold yellow]Enter Command (list, ping, exit)[/bold yellow]")
        message_queue.put(("command", command))
        pub.put(command)
        if command.strip().lower() == "exit":
            break

def main_interface():
    device_status = dict(devices)
    command_log = []

    def render_log():
        log_table = Table(title="Command Log", expand=True)
        log_table.add_column("Command", style="yellow", no_wrap=True)
        log_table.add_column("Response", style="white")

        for cmd, resp in command_log[-10:]:
            log_table.add_row(cmd, resp)
        return log_table

    def render():
        layout = Table.grid(padding=(1, 1))
        layout.add_row(render_table(device_status))
        layout.add_row(render_log())
        return layout

    with Live(render(), refresh_per_second=4) as live:
        while True:
            try:
                msg_type, payload = message_queue.get(timeout=0.5)
                if msg_type == "update":
                    device_status.update(payload)
                elif msg_type == "command":
                    cmd = payload.strip().lower()
                    if cmd == "list":
                        command_log.append(("list", "Displayed current device list"))
                    elif cmd == "ping":
                        command_log.append(("ping", "Simulated ping sent to all devices"))
                    elif cmd == "exit":
                        command_log.append(("exit", "Exiting..."))
                        break
                    else:
                        command_log.append((cmd, "Unknown command"))
                live.update(render())
            except queue.Empty:
                continue

if __name__ == "__main__":
    try:
        threading.Thread(target=start_iff_listener, daemon=True).start()
        threading.Thread(target=ttl_monitor, daemon=True).start()
        threading.Thread(target=command_interface, daemon=True).start()
        main_interface()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user.[/red]")
        sys.exit(0)
