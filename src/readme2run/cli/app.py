import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="readme2run",
        description="Read a repository README and run it.",
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("run", help="Run a repository from its URL")
    commands.add_parser("runs", help="List past runs")
    commands.add_parser("show", help="Show one run")
    parser.parse_args()


if __name__ == "__main__":
    main()
