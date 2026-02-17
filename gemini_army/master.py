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
    Based on the user's request: '{command}', define a team of specialized agents and a sequence of granular, atomic tasks to accomplish the goal.
    For each task, clearly specify:
    1. The "agent" responsible (must be one of the roles in the "team" list).
    2. The "task" (a specific, actionable instruction for that agent).
    3. The "expected_output" (a clear, CONCISE description of what the agent should produce upon completion. If generating code or content, specify file paths, and output a brief summary, NOT the full content. E.g., "a JSON object summarizing the design," "create HTML/CSS files in the 'frontend/' directory, and briefly confirm completion").

    Output the result as a single, full, valid JSON object with two keys, and nothing else:
    1. "team": A list of strings, where each string is a role for an agent (e.g., "frontend_developer", "ui_ux_designer", "backend_engineer", "qa_tester", "devops_engineer").
    2. "plan": A list of JSON objects, where each object has "agent", "task", and "expected_output" keys.

    Example:
    {{
      "team": ["project_manager", "ui_ux_designer", "frontend_developer", "backend_developer", "qa_tester"],
      "plan": [
        {{"agent": "project_manager", "task": "Initial project setup and scope definition. List all necessary directories and initial file structures.", "expected_output": "A JSON object describing project structure and initial setup files."}},
        {{"agent": "ui_ux_designer", "task": "Design wireframes and mockups for homepage, about, projects, and contact pages.", "expected_output": "Create 'design/wireframes.md' and 'design/mockups.md' files describing the UI/UX."}},
        {{"agent": "backend_developer", "task": "Develop a RESTful API for project data and contact form submissions. Focus on core endpoints.", "expected_output": "Create 'backend/' directory with Python/Node.js files implementing the API, and output API endpoints in a JSON object."}},
        {{"agent": "frontend_developer", "task": "Build the static HTML/CSS structure based on UI/UX designs.", "expected_output": "Create 'frontend/' directory with HTML/CSS files."}},
        {{"agent": "frontend_developer", "task": "Integrate frontend with backend API for dynamic project display and contact form.", "expected_output": "Update 'frontend/' files, and output a JSON object confirming successful integration."}},
        {{"agent": "qa_tester", "task": "Perform initial functional testing of all pages and API endpoints.", "expected_output": "A JSON object summarizing test results, bugs found, and suggestions for improvement."}}
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
        print(f"Gemini stdout:\n{process.stdout}")
        print(f"Gemini stderr:\n{process.stderr}")
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
    slave_processes_info = []
    
    print(f"Master Agent: Assembling team of {len(team_roles)} agents: {', '.join(team_roles)}")
    for i, role in enumerate(team_roles):
        slave_id = f"slave_{i}"
        
        # Write the role file immediately after determining the role for this slave_id
        role_file = config.COMM_DIR / f"{slave_id}.role"
        with open(role_file, "w") as f:
            f.write(f"You are an expert {role}. Your goal is to be a world-class specialist in your domain.")

        process = await asyncio.create_subprocess_exec(
            "python", "-m", "gemini_army.main", "slave", f"listen --id {slave_id}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE # Capture stdout/stderr for potential debugging
        )
        slave_processes_info.append({"id": slave_id, "role": role, "process": process})
        print(f"Launched {slave_id} with role: {role}")

    # Give slaves a moment to start up
    await asyncio.sleep(2)

    # Execute the plan
    for i, step in enumerate(plan["plan"]):
        agent_role = step["agent"]
        task = step["task"]
        
        # Find a slave with the required role
        slave_to_assign = next((s for s in slave_processes_info if s["role"] == agent_role), None)

        if not slave_to_assign:
            print(f"Master Agent: No agent found with role '{agent_role}' for step {i+1}. Skipping.")
            continue

        slave_id = slave_to_assign["id"]
        print(f"\n--- Step {i+1}: Assigning task to {slave_id} ({agent_role}) ---")
        print(f"Task: {task}")
        
        result = await send_command_to_slave(slave_id, task) # Removed role parameter
        
        print(f"--- Result from {slave_id} ---")
        print(result)
        print(f"--- End of Step {i+1} ---")


    # Terminate slave processes
    print("\nMaster Agent: All tasks completed. Terminating slave agents.")
    for slave in slave_processes_info:
        slave["process"].terminate()
    
    await asyncio.gather(*[s["process"].wait() for s in slave_processes_info])
    print("All slaves terminated.")

async def send_command_to_slave(slave_id: str, command: str): # Removed role parameter
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
