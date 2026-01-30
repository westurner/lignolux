#!/usr/bin/env python3
"""
manage.py -- a port of the Makefile tasks
"""

import argparse
import subprocess
import sys
import os
import logging


# Setup Logging
class ColorFormatter(logging.Formatter):
    RED = "\033[91m"
    RESET = "\033[0m"

    def format(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"{self.RED}{record.msg}{self.RESET}"
        return super().format(record)


logger = logging.getLogger("manage")


def setup_logging(log_file=None, verbose=False, quiet=False):
    """Configure logging handlers."""
    logger.setLevel(logging.DEBUG)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    if quiet:
        ch.setLevel(logging.ERROR)
    elif verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

    ch.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)

    # File Handler
    if log_file:
        log_path = os.path.dirname(log_file)
        if log_path:
            os.makedirs(log_path, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(fh)


def run_command(command, cwd=None):
    """Utility to run a shell command and exit on failure."""
    logger.info(
        f"Executing: {' '.join(command) if isinstance(command, list) else command}"
    )
    try:
        # Use shell=True for strings, or pass list directly
        is_shell = isinstance(command, str)
        subprocess.check_call(command, shell=is_shell, cwd=cwd)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError as e:
        logger.error(f"{e}")
        sys.exit(1)


def build_docs():
    """Build sphinx documentation."""
    run_command(["make", "-C", "docs", "html"])


def aggregate_data(input_dir=None, output=None):
    """Run the technical data aggregation tool."""
    script_path = os.path.join("tools", "aggregate_technical_data.py")
    cmd = [sys.executable, script_path]
    if input_dir:
        cmd.extend(["--input-dir", input_dir])
    if output:
        cmd.extend(["--output", output])
    run_command(cmd)


def transform_md(indir=None, outdir=None):
    """Run transform-md on the chatoverlay data."""
    command = [
        "transform-md",
        "--indir",
        indir or "data/chatoverlay/chats__all/",
        "--outdir",
        outdir or "data/chats_ipynb/",
        "--transform-cell-split",
        "m1",
        "--out-format=myst,ipynb,chatexport_abc1",
    ]
    run_command(command)


def run_tests():
    """Run technical data aggregation and markdown transformation."""
    logger.info("Running integrated tests...")
    aggregate_data()
    transform_md()


def run_pytest():
    """Run pytest suite."""
    run_command(["pytest", "."])


def main():
    parser = argparse.ArgumentParser(
        description="Management script for the Sustainable Factory project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Decrease output verbosity"
    )
    parser.add_argument("--log-output", help="Path to log file")

    subparsers = parser.add_subparsers(dest="command", help="The command to execute")

    # Docs command
    subparsers.add_parser(
        "docs",
        help="Build HTML documentation using Sphinx",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Aggregate command
    agg_parser = subparsers.add_parser(
        "aggregate",
        help="Aggregate technical and economic data from MyST files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    agg_parser.add_argument(
        "--input-dir",
        default="data/chats",
        help="Directory containing input .md and .json files",
    )
    agg_parser.add_argument(
        "--output", default="docs/tables_and_figures.myst.md", help="Output file path"
    )

    # Transform command
    trans_parser = subparsers.add_parser(
        "transform",
        help="Transform markdown files in data/chatoverlay/chats__all/",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    trans_parser.add_argument(
        "--indir", default="data/chatoverlay/chats__all/", help="Input directory"
    )
    trans_parser.add_argument(
        "--outdir", default="data/chats_ipynb/", help="Output directory"
    )

    # Test command (composite)
    subparsers.add_parser(
        "test",
        help="Run aggregate and transform (composite test)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Pytest command
    subparsers.add_parser(
        "pytest",
        help="Run the full pytest suite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    args = parser.parse_args()

    setup_logging(log_file=args.log_output, verbose=args.verbose, quiet=args.quiet)

    if args.command == "docs":
        build_docs()
    elif args.command == "aggregate":
        aggregate_data(input_dir=args.input_dir, output=args.output)
    elif args.command == "transform":
        transform_md(indir=args.indir, outdir=args.outdir)
    elif args.command == "test":
        run_tests()
    elif args.command == "pytest":
        run_pytest()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
