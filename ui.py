from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich.panel import Panel
import threading
import time
import queue
import random
import sys

import zenoh

devices = {
    "Device-A": False,
    "Device-B": False,
    "Device-C": False
}

message_queue = queue.Queue()
console = Console()

def iff_worker():
    while True:
        for device in devices:
            devices[device] = random.choice([True, False])
        message_queue.put(("update", dict(devices)))
        time.sleep(3)

def render_table(device_status):
    table = Table(title="Connected Devices")
    table.add_column("Device", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")

    for name, status in device_status.items():
        table.add_row(name, "🟢 Online" if status else "🔴 Offline")
    return table

def command_interface():
    config = zenoh.Config()
    session = zenoh.open(config)

    pub = session.declare_publisher('global/COMMAND')

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
    # Start the IFF worker thread
    threading.Thread(target=iff_worker, daemon=True).start()

    # Start command line input in the main thread (important for terminal input)
    try:
        threading.Thread(target=command_interface, daemon=True).start()
        main_interface()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user.[/red]")
        sys.exit(0)
