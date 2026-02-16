import asyncio
import os
import time
import subprocess
import json
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
    role_file = config.COMM_DIR / f"{slave_id}.role"
    shared_context_file = config.COMM_DIR / "shared_context.json"

    system_prompt = "You are a helpful assistant." # Default role

    while True:
        # Load system prompt
        if role_file.exists():
            with open(role_file, "r") as f:
                system_prompt = f.read().strip()
        
        if cmd_file.exists():
            try:
                with open(cmd_file, "r") as f:
                    command = f.read()
                
                print(f"Slave {slave_id} ({system_prompt.splitlines()[0]}): Received command: {command}")

                # Load shared context
                shared_context = {}
                if shared_context_file.exists():
                    try:
                        with open(shared_context_file, "r") as f:
                            shared_context = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Slave {slave_id}: Warning: shared_context.json is not valid JSON. Ignoring.")
                        shared_context = {}

                full_prompt = f"{system_prompt}\n\nCurrent Shared Context: {json.dumps(shared_context, indent=2)}\n\nTask: {command}"
                
                # Execute the command using the gemini cli
                try:
                    process = subprocess.run(
                        ["gemini", "-p", full_prompt, "--approval-mode", "yolo"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    gemini_output = process.stdout
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    gemini_output = f"Error executing command: {e}"

                # Try to update shared context from Gemini's output
                try:
                    output_json = json.loads(gemini_output)
                    # Update shared context, allowing new keys and overwriting existing ones
                    shared_context.update(output_json)
                    with open(shared_context_file, "w") as f:
                        json.dump(shared_context, f, indent=2)
                    print(f"Slave {slave_id}: Updated shared context.")
                except json.JSONDecodeError:
                    print(f"Slave {slave_id}: Gemini output was not JSON. Not updating shared context.")
                    # If not JSON, just pass the raw output as the result
                
                with open(res_file, "w") as f:
                    f.write(gemini_output)

            finally:
                # Clean up the command file
                if cmd_file.exists():
                    os.remove(cmd_file)
        
        # A more robust slave would have a way to be shut down.
        # For now, it will loop indefinitely.
        time.sleep(0.5)
