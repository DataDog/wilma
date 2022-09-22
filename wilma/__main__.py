import argparse
import os
import sys

from wilma import __version__


def main():
    parser = argparse.ArgumentParser(
        # description="",
        prog="wilma",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, type=str, help="Command string to execute."
    )
    parser.add_argument(
        "-p",
        "--prefix",
        help="The prefix to use for installing dependencies",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Pass a specific configuration file. Defaults to the one in the current directory",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s " + __version__,
    )
    args = parser.parse_args()

    root_dir = os.path.dirname(__file__)

    bootstrap_dir = os.path.join(root_dir, "_bootstrap")

    if not args.command:
        parser.print_help()
        sys.exit(1)

    executable = args.command[0]
    env = dict(os.environ)
    if args.config:
        env["WILMAFILE"] = args.config
    if args.prefix:
        env["WILMAPREFIX"] = args.prefix
    if args.verbose:
        env["WILMAVERBOSE"] = "1"

    python_path = os.path.pathsep.join(sys.path)
    env["PYTHONPATH"] = (
        os.path.pathsep.join((bootstrap_dir, python_path))
        if python_path
        else bootstrap_dir
    )

    try:
        os.execvpe(executable, args.command, env)  # TODO: Cross-platform?
    except (OSError, PermissionError):
        print(
            "wilma: executable '%s' does not have executable permissions.\n"
            % executable
        )
        parser.print_usage()
        sys.exit(1)


main()
