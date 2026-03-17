import subprocess
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs")
LOG_FILE = os.path.join(LOG_DIR, "commands.txt")

os.makedirs(LOG_DIR, exist_ok=True)

print(f"Command logger ON — writing to: {LOG_FILE}")
print("Type 'exit' or press Ctrl+C to stop.\n")

while True:
    try:
        cmd = input(">> ")
        if cmd.strip() == "":
            continue
        if cmd.strip().lower() == "exit":
            print("Logger OFF.")
            break

        with open(LOG_FILE, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {cmd}\n")

        subprocess.run(cmd, shell=True)

    except KeyboardInterrupt:
        print("\nLogger OFF.")
        break
