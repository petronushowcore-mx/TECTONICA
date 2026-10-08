"""Run pinned XIV/XV, Identity, PoA, recomposition, Severance, Person, common-control and Double Fibre connections."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LAYERS = ("XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre")


class Refusal(Exception):
    pass


def git_bytes(root, *args):
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith("GIT_")}
    try:
        result = subprocess.run(["git", "--no-lazy-fetch", "--no-replace-objects", "--no-optional-locks",
                                 "-c", "core.fsmonitor=false",
                                 "-C", str(root), *args], capture_output=True, env=environment)
    except OSError as exc:
        raise Refusal("GIT_UNAVAILABLE") from exc
    if result.returncode:
        raise Refusal("GIT_FAILED: " + str(root) + ": " +
                      result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def git(root, *args):
    return git_bytes(root, *args).decode("utf-8").rstrip("\r\n")


def checked_layers(root):
    root = Path(root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Refusal("PROJECT_ROOT_REQUIRED")
    selected = {}
    for name in LAYERS:
        relative = "layers/" + name
        record = git(root, "ls-tree", "HEAD", "--", relative)
        parts = record.split()
        kind = ["040000", "tree"] if name == "ProbeVI" else ["160000", "commit"]
        if (len(parts) != 4 or parts[0:2] != kind
                or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", parts[2])
                or parts[3] != relative):
            raise Refusal("PIN_REQUIRED: " + name)
        expected = git(root, "rev-parse", "HEAD") if name == "ProbeVI" else parts[2]
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected):
            raise Refusal("PIN_REQUIRED: " + name)
        directory = root / relative
        repository = root if name == "ProbeVI" else directory
        scope = ["--", relative] if name == "ProbeVI" else []
        if not directory.is_dir():
            raise Refusal("DEPENDENCY_MISSING: " + name)
        if Path(git(directory, "rev-parse", "--show-toplevel")).resolve() != repository:
            raise Refusal("DEPENDENCY_ROOT: " + name)
        if git(directory, "rev-parse", "HEAD") != expected:
            raise Refusal("REVISION_MISMATCH: " + name)
        flags = git(repository, "ls-files", "-v", "-z", *scope).split("\0")
        if any(row[:1].islower() or row.startswith("S ") for row in flags if row):
            raise Refusal("HIDDEN_INDEX_FLAGS: " + name)
        dirty = git(repository, "status", "--porcelain=v1", "--untracked-files=all", "--ignored", *scope)
        if dirty:
            raise Refusal("DEPENDENCY_DIRTY: " + name)
        selected[name] = (directory, expected)
    if not (selected["XV"][0] / "harness/xiv_stitch.py").is_file():
        raise Refusal("RUNNER_MISSING: XV")
    for source in ("switch_transport.py", "emergence_verify.py", "emergence_certificate.json"):
        if not (selected["Identity"][0] / "harness" / source).is_file():
            raise Refusal("SOURCE_MISSING: Identity/" + source)
    if not (selected["PoA"][0] / "harness/seam_audit.py").is_file():
        raise Refusal("SOURCE_MISSING: PoA/seam_audit.py")
    if not (selected["Person"][0] / "person_harness.py").is_file():
        raise Refusal("SOURCE_MISSING: Person/person_harness.py")
    if not (selected["ProbeVI"][0] / "harness/probe_vi.py").is_file():
        raise Refusal("SOURCE_MISSING: ProbeVI/harness/probe_vi.py")
    if not (selected["DoubleFibre"][0] / "harness/double_fibre_audit.py").is_file():
        raise Refusal("SOURCE_MISSING: DoubleFibre/harness/double_fibre_audit.py")
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
        commands = [
            command + [str(ROOT / "pinned_sources.py")],
            command + [str(ROOT / "identity_stitch.py")],
            command + [str(ROOT / "poa_stitch.py")],
            command + [str(ROOT / "recomposition_stitch.py")],
            command + [str(ROOT / "severance_stitch.py"), "--teeth"],
            command + [str(ROOT / "person_stitch.py")],
            command + [str(ROOT / "common_control_stitch.py")],
            command + [str(ROOT / "double_fibre_stitch.py")],
        ]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for child in commands:
            result = subprocess.run(child, cwd=ROOT, env=environment, check=False)
            if result.returncode:
                return result.returncode
        return 0
    except (Refusal, OSError) as exc:
        print("TECTONICA: REFUSED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

