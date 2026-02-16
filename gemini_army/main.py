import argparse
import asyncio
from . import master
from . import slave

def main():
    parser = argparse.ArgumentParser(description="Gemini Multi-Agent CLI")
    subparsers = parser.add_subparsers(dest="role", required=True)

    master_parser = subparsers.add_parser("master", help="Run as master agent")
    master_parser.add_argument("command", help="Command for the master agent")

    slave_parser = subparsers.add_parser("slave", help="Run as slave agent")
    slave_parser.add_argument("command", help="Command for the slave agent")

    args = parser.parse_args()

    if args.role == "master":
        asyncio.run(master.run_master(args.command))
    elif args.role == "slave":
        slave.run_slave(args.command)

if __name__ == "__main__":
    main()
