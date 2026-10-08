"""Run copied adapter mutations in separate interpreters; pinned files are never changed."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
import tectonica
import common_control_stitch as app

BREAKS = (
    ("C_CATALOGUE", "app", 'rows[fixture.name] = {"fixture": fixture, "proof": proof}',
     'rows[fixture.name] = {"fixture": fixture, "proof": proof}\n        if fixture.name == "aligned":\n            rows.pop("aligned")'),
    ("C_CERTIFIED_CATALOGUE", "adapter", "base.aligned_b", "(Q(-2), Q(-1), Q(0))"),
    ("C_UNSUPPORTED", "adapter", "if f not in declared:", "if False:"),
    ("C_COMMON_TARGET", "app", 'if status == "PROVED_CANONICAL_OBSTRUCTION":\n        return False',
     'if status == "PROVED_CANONICAL_OBSTRUCTION":\n        return True'),
    ("C_LOCAL_CERTIFICATES", "app", 'return row["proof"]["local_viability"]',
     'return (row["proof"]["local_viability"][0], False)'),
    ("C_STATIONARY_WITNESSES", "adapter", '"rates": tuple(map(str, rates))',
     '"rates": ("0", "0", "1")'),
    ("C_LOCAL_FIBRE", "poa", "return bool(fibres) and all(len(values) == 1 for values in fibres.values())",
     "return bool(fibres)"),
    ("C_FULL_PROFILE", "app", "return (f.a, f.b, f.h_rows, f.h, f.x0, f.u_bounds, f.horizon, f.strategy, f.controls)",
     "return f.h_rows"),
    ("C_BOOLEAN_DOMAIN", "app", 'raise tectonica.Refusal("COMMON_CONTROL_TARGET_UNESTABLISHED")',
     "return False"),
    ("C_EXECUTED_COUNT", "app", "checks.append(marker)",
     'if marker != "C_BOOLEAN_DOMAIN":\n            checks.append(marker)'),
)
# One identifier-renaming positive control and a same-site reachability control.
CONTROLS = (
    ("SURVIVE", "app", "names = tuple(rows)", "identifiers = tuple(rows)"),
    ("REACH", "app", "names = tuple(rows)", "names = None"),
)

def copied(module, body):
    clone = ModuleType(module.__name__ + "_copied")
    clone.__file__ = module.__file__
    sys.modules[clone.__name__] = clone
    exec(compile(body, module.__file__, "exec"), clone.__dict__)
    return clone

def replace_one(body, old, new):
    old, new = old.replace("\\n", "\n"), new.replace("\\n", "\n")
    if body.count(old) != 1:
        raise RuntimeError("MUTATION_ANCHOR_COUNT: " + str(body.count(old)))
    return body.replace(old, new, 1)

def one_case(index):
    selected = tectonica.checked_layers(Path(__file__).resolve().parent)
    probe, poa = app.load(selected), app.load_poa(selected)
    active = copied(app, Path(app.__file__).read_text(encoding="utf-8-sig"))
    if index is not None:
        entries = BREAKS + CONTROLS
        expected, subject, old, new = entries[index]
        module = {"app": app, "adapter": app.adapter, "poa": poa}[subject]
        body = Path(module.__file__).read_text(encoding="utf-8-sig")
        if expected == "SURVIVE":
            # Consistent renaming of the exact local identifier, including consumers.
            body = body.replace("names", "identifiers")
        else:
            body = replace_one(body, old, new)
        mutant = copied(module, body)
        if subject == "app":
            active = mutant
        elif subject == "adapter":
            active.adapter = mutant
        else:
            poa = mutant
    try:
        rows = active.catalogue(probe)
        checks = active.verify(probe, poa, rows)
    except tectonica.Refusal as error:
        print(json.dumps({"first_red": str(error)}))
        return 1
    except Exception as error:
        print(json.dumps({"crash": type(error).__name__, "detail": str(error)}))
        return 2
    print(json.dumps({"first_red": None, "checks": checks, "check_count": len(checks)}))
    return 0

def run_case(index, optimized):
    command = [sys.executable, "-B"]
    if optimized:
        command.append("-O")
    command += [str(Path(__file__).resolve()), "--case", "base" if index is None else str(index)]
    env = dict(os.environ)
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, capture_output=True, text=True,
                            stdin=subprocess.DEVNULL, timeout=120, env=env)
    try:
        record = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError("MUTATION_RUN_UNMEASURED: " + result.stderr)
    return result.returncode, record

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--case":
        return one_case(None if sys.argv[2] == "base" else int(sys.argv[2]))
    executed = 0
    for optimized in (False, True):
        status, record = run_case(None, optimized)
        if status or record.get("first_red") is not None or record.get("check_count") != 9:
            raise RuntimeError("BASELINE_NOT_ESTABLISHED: " + str(record))
        executed += 1
        for index, (expected, _, _, _) in enumerate(BREAKS + CONTROLS):
            status, record = run_case(index, optimized)
            if expected == "SURVIVE":
                good = status == 0 and record.get("first_red") is None and record.get("check_count") == 9
            elif expected == "REACH":
                good = status != 0 and ("first_red" in record or "crash" in record)
            else:
                good = status == 1 and record.get("first_red") == expected
            if not good:
                raise RuntimeError("MUTATION_UNPROVED: " + expected + " " + str(record))
            executed += 1
            print(expected + " " + ("optimized" if optimized else "normal"))
    if executed != 26:
        raise RuntimeError("MUTATION_EXECUTED_COUNT: " + str(executed))
    print("COMMON_CONTROL_MUTATIONS: 26/26")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

