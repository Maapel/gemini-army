import asyncio
import os
import time
import subprocess
from . import config

def run_slave(command: str):
    parts = command.split()
    if parts[0] == "listen" and "--id" in parts:
        slave_id_index = parts.index("--id") + 1
        if slave_id_index < len(parts):
            slave_id = parts[slave_id_index]
            print(f"Slave {slave_id} listening for commands.")
            listen_for_commands(slave_id)
        else:
            print("Error: --id flag provided without a value.")
    else:
        print(f"Slave executing command: {command}")
        # For direct command execution (not listening)
        result = f"Executed: {command}"
        print(result)

def listen_for_commands(slave_id: str):
    cmd_file = config.COMM_DIR / f"{slave_id}.cmd"
    res_file = config.COMM_DIR / f"{slave_id}.res"

    while True:
        if cmd_file.exists():
            try:
                with open(cmd_file, "r") as f:
                    command = f.read()
                
                print(f"Slave {slave_id} received command: {command}")
                
                # Execute the command using the gemini cli
                try:
                    process = subprocess.run(
                        ["gemini", "-p", command, "--approval-mode", "yolo"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    result = process.stdout
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    result = f"Error executing command: {e}"

                with open(res_file, "w") as f:
                    f.write(result)

            finally:
                # Clean up the command file
                if cmd_file.exists():
                    os.remove(cmd_file)
        
        # A more robust slave would have a way to be shut down.
        # For now, it will loop indefinitely.
        time.sleep(0.5)
