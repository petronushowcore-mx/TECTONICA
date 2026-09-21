"""Run the XIV/XV construction from the dependency commits recorded in HEAD."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LAYERS = ("XIV", "XV")


class Refusal(Exception):
    pass


def git(root, *args):
    try:
        result = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args],
                                capture_output=True, text=True, encoding="utf-8")
    except OSError as exc:
        raise Refusal("GIT_UNAVAILABLE") from exc
    if result.returncode:
        raise Refusal("GIT_FAILED: " + str(root) + ": " + result.stderr.strip())
    return result.stdout.rstrip("\r\n")


def checked_layers(root):
    root = Path(root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Refusal("PROJECT_ROOT_REQUIRED")
    selected = {}
    for name in LAYERS:
        relative = "layers/" + name
        record = git(root, "ls-tree", "HEAD", "--", relative)
        parts = record.split()
        if (len(parts) != 4 or parts[0:2] != ["160000", "commit"]
                or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", parts[2])
                or parts[3] != relative):
            raise Refusal("PIN_REQUIRED: " + name)
        expected = parts[2]
        directory = root / relative
        if not directory.is_dir():
            raise Refusal("DEPENDENCY_MISSING: " + name)
        if Path(git(directory, "rev-parse", "--show-toplevel")).resolve() != directory:
            raise Refusal("DEPENDENCY_ROOT: " + name)
        if git(directory, "rev-parse", "HEAD") != expected:
            raise Refusal("REVISION_MISMATCH: " + name)
        flags = git(directory, "ls-files", "-v", "-z").split("\0")
        if any(row[:1].islower() or row.startswith("S ") for row in flags if row):
            raise Refusal("HIDDEN_INDEX_FLAGS: " + name)
        dirty = git(directory, "status", "--porcelain=v1", "--untracked-files=all", "--ignored")
        if dirty:
            raise Refusal("DEPENDENCY_DIRTY: " + name)
        selected[name] = (directory, expected)
    if not (selected["XV"][0] / "harness/xiv_stitch.py").is_file():
        raise Refusal("RUNNER_MISSING: XV")
    return selected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="check dependency commits and cleanliness")
    args = parser.parse_args(argv)
    try:
        selected = checked_layers(ROOT)
        for name, (_, revision) in selected.items():
            print(name + "_COMMIT " + revision, flush=True)
        if args.check_only:
            return 0
        command = [sys.executable, "-B"]
        if sys.flags.optimize:
            command.append("-" + "O" * sys.flags.optimize)
        command += [str(selected["XV"][0] / "harness/xiv_stitch.py"),
                    "--xiv-root", str(selected["XIV"][0]), "--teeth"]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode
    except (Refusal, OSError) as exc:
        print("TECTONICA: REFUSED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
