from pathlib import Path
import os

# Number of slave agents to launch
NUM_SLAVES = 5

# Directory for inter-agent communication
COMM_DIR = Path("/data/data/com.termux/files/home/.gemini/tmp/be36aa850ed33336ee9b50e53a9026eb7feb9c91da12c0a4057f4cc20da851ec/gemini-army-comm")

def create_comm_dirs():
    """Create the communication directory if it doesn't exist."""
    os.makedirs(COMM_DIR, exist_ok=True)
