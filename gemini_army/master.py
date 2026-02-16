import asyncio
import subprocess
from . import config

async def run_master(command: str):
    print(f"Master agent executing command: {command}")
    
    # Create communication directories
    config.create_comm_dirs()

    # Launch slave agents
    slave_processes = []
    for i in range(config.NUM_SLAVES):
        slave_id = f"slave_{i}"
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "gemini_army.main", "slave", f"listen --id {slave_id}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        slave_processes.append((slave_id, process))
        print(f"Launched {slave_id}")

    # Give slaves a moment to start up
    await asyncio.sleep(2)

    # Send a command to the first slave
    tasks = [send_command_to_slave(slave_processes[0][0], command)]
    
    results = await asyncio.gather(*tasks)

    print(f"Result from {slave_processes[0][0]}: {results[0]}")

    # Terminate slave processes
    for _, process in slave_processes:
        process.terminate()
    
    await asyncio.gather(*[p.wait() for _, p in slave_processes])
    print("All slaves terminated.")

async def send_command_to_slave(slave_id: str, command: str):
    cmd_file = config.COMM_DIR / f"{slave_id}.cmd"
    with open(cmd_file, "w") as f:
        f.write(command)

    # Wait for the result
    res_file = config.COMM_DIR / f"{slave_id}.res"
    while not res_file.exists():
        await asyncio.sleep(0.1)

    with open(res_file, "r") as f:
        result = f.read()

    # Clean up the result file
    res_file.unlink()

    return result
