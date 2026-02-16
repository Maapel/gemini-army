import asyncio
import subprocess
import json
from . import config

async def create_project_plan(command: str):
    """
    Calls Gemini to create a project plan based on the user's command.
    """
    print("Master Agent: Creating a project plan...")
    planning_prompt = f"""
    Based on the user's request: '{command}', define a team of agents and a sequence of tasks to accomplish the goal.
    Output the result as a single JSON object with two keys:
    1. "team": A list of strings, where each string is a role for an agent (e.g., "frontend_developer").
    2. "plan": A list of JSON objects, where each object has an "agent" key (the role from the team list) and a "task" key (a specific instruction for that agent).

    Example:
    {{
      "team": ["project_manager", "backend_developer", "frontend_developer"],
      "plan": [
        {{"agent": "project_manager", "task": "Break down the feature into smaller tickets."}},
        {{"agent": "backend_developer", "task": "Implement the API endpoints based on the tickets."}},
        {{"agent": "frontend_developer", "task": "Build the UI to consume the new API."}}
      ]
    }}
    """
    try:
        process = subprocess.run(
            ["gemini", "-p", planning_prompt, "--approval-mode", "yolo"],
            capture_output=True,
            text=True,
            check=True
        )
        # Clean the output to extract only the JSON
        json_str = process.stdout[process.stdout.find('{'):process.stdout.rfind('}')+1]
        plan = json.loads(json_str)
        print("Master Agent: Project plan created successfully.")
        return plan
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Master Agent: Error creating project plan: {e}")
        return None

async def run_master(command: str):
    print(f"Master Agent: Orchestrating command: {command}")
    
    plan = await create_project_plan(command)
    if not plan or "team" not in plan or "plan" not in plan:
        print("Master Agent: Could not generate a valid project plan. Aborting.")
        return

    config.create_comm_dirs()
    # Initialize shared context
    with open(config.COMM_DIR / "shared_context.json", "w") as f:
        json.dump({"project_goal": command, "status": "started"}, f)

    team_roles = plan["team"]
    slave_processes = []
    
    print(f"Master Agent: Assembling team of {len(team_roles)} agents: {', '.join(team_roles)}")
    for i, role in enumerate(team_roles):
        slave_id = f"slave_{i}"
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "gemini_army.main", "slave", f"listen --id {slave_id}",
        )
        slave_processes.append({"id": slave_id, "role": role, "process": process})
        print(f"Launched {slave_id} with role: {role}")

    # Give slaves a moment to start up
    await asyncio.sleep(2)

    # Execute the plan
    for i, step in enumerate(plan["plan"]):
        agent_role = step["agent"]
        task = step["task"]
        
        # Find a slave with the required role
        slave_to_assign = next((s for s in slave_processes if s["role"] == agent_role), None)

        if not slave_to_assign:
            print(f"Master Agent: No agent found with role '{agent_role}' for step {i+1}. Skipping.")
            continue

        slave_id = slave_to_assign["id"]
        print(f"\n--- Step {i+1}: Assigning task to {slave_id} ({agent_role}) ---")
        print(f"Task: {task}")
        
        result = await send_command_to_slave(slave_id, slave_to_assign["role"], task)
        
        print(f"--- Result from {slave_id} ---")
        print(result)
        print(f"--- End of Step {i+1} ---")


    # Terminate slave processes
    print("\nMaster Agent: All tasks completed. Terminating slave agents.")
    for slave in slave_processes:
        slave["process"].terminate()
    
    await asyncio.gather(*[s["process"].wait() for s in slave_processes])
    print("All slaves terminated.")

async def send_command_to_slave(slave_id: str, role: str, command: str):
    # Write the role file
    role_file = config.COMM_DIR / f"{slave_id}.role"
    with open(role_file, "w") as f:
        f.write(f"You are an expert {role}. Your goal is to be a world-class specialist in your domain.")

    # Write the command file
    cmd_file = config.COMM_DIR / f"{slave_id}.cmd"
    with open(cmd_file, "w") as f:
        f.write(command)

    # Wait for the result
    res_file = config.COMM_DIR / f"{slave_id}.res"
    while not res_file.exists():
        await asyncio.sleep(0.5)

    with open(res_file, "r") as f:
        result = f.read()

    # Clean up the result file
    res_file.unlink()

    return result
