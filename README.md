# Gemini Army

This repository contains the codebase for the Gemini Army project, a multi-agent CLI (Command Line Interface) for Gemini.
This project was developed on a phone using Gemini CLI on Termux.

## Project Overview

The Gemini Army project is designed as a multi-agent Command Line Interface for Gemini, likely for distributed task processing or AI agent orchestration. It employs a master-worker architecture and includes an associated portfolio website (`portfolio-website/`).

## Project Structure

-   `gemini_army/`: Contains the core Python-based multi-agent CLI system.
    -   `main.py`: The main entry point for the CLI application.
    -   `master.py`: Implements the master component of the AI architecture.
    -   `slave.py`: Implements the worker (slave) component of the AI architecture.
    -   `config.py`: Configuration settings for the CLI system.
-   `portfolio-website/`: Contains the code for a web interface.
    -   `backend/`: Backend components of the website.
    -   `frontend/`: Frontend components of the website.
-   `pyproject.toml`: Project configuration and dependency management for the Python parts.
-   `README.md`: This file.

## Getting Started

To get a local copy up and running, follow these steps.

### Prerequisites

-   Python 3.7 or higher

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Maapel/gemini-army.git
    cd gemini-army
    ```
2.  Install Python dependencies:
    ```bash
    pip install -e .
    ```

## Usage

You can run the CLI application using:
```bash
gemini-army
```
Further details on running the master, slave components, and the web interface will be added here.

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
