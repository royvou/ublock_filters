"""Run the repository's fast checks; --fix also applies safe formatting fixes.

Run with `uv run --locked python scripts/check.py`. Requires Git and uv.
Live Firefox verification is a separate command.
"""

import argparse
import ast
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--fix",
        action="store_true",
        help="Apply safe Python and Markdown fixes before checking",
    )
    args = cli.parse_args()
    files = sorted(
        set(
            subprocess.check_output(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                cwd=ROOT,
            )
            .decode()
            .strip("\0")
            .split("\0")
        )
    )
    # git ls-files includes tracked deletions; validate the files still present.
    files = [name for name in files if (ROOT / name).is_file()]
    markdown = [name for name in files if name.endswith(".md")]
    yaml = [name for name in files if name.endswith((".yml", ".yaml"))]
    for name in files:
        path = ROOT / name
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=name)
        elif path.suffix == ".toml":
            with path.open("rb") as stream:
                tomllib.load(stream)
        elif path.suffix == ".svg":
            ET.parse(path)
    run("uv", "lock", "--check")
    run("uv", "lock", "--check", "--script", "scripts/verify-firefox.py")
    run("ruff", "check", ".", *(["--fix"] if args.fix else []))
    run("ruff", "format", ".", *([] if args.fix else ["--check"]))
    run("mypy", "scripts")
    if markdown:
        run("mdformat", *([] if args.fix else ["--check"]), *markdown)
        run("pymarkdown", "scan", *markdown)
    if yaml:
        run("yamllint", "--strict", *yaml)
    run("actionlint", "-shellcheck=", "-pyflakes=")
    run(sys.executable, "scripts/check-filters.py")
    run(sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests")
    print("All repository checks passed.")


if __name__ == "__main__":
    main()
