"""Break only copies of the local finite Severance adapter; never original layers."""
import ast
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types

SUBJECT = Path(__file__).with_name("severance_stitch.py")
EXPECTED_BREAKS = 14
BREAKS = [
    ("exact_budget_boundary", "return model.capacity - phi_gamma(model) > 0",
     "return model.capacity - phi_gamma(model) >= 0", "Treat exhausted budget as positive."),
    ("loss_distinct_from_unknown", 'return "insufficient_information"',
     'return "confirmed_budget_loss"', "Convert a mixed fibre into asserted loss."),
    ("capacity_excision_profile", "delta = 1 - int(criterion(excised))",
     "delta = 0", "Ignore actual functional failure after deletion."),
    ("ambiguity_without_function_loss", "delta = 1 - int(criterion(excised))",
     "delta = 1", "Report functional loss where hidden capacity keeps the function."),
    ("determinate_negative_is_decidable",
     "return bool(completions) and len({budget_positive(m) for m in completions}) == 1",
     "return bool(completions) and all(budget_positive(m) for m in completions)",
     "Mistake a determinate negative answer for an unusable budget checker."),
    ("model_edge_loss_despite_observation_admit",
     "edges = tuple(e for e in model.edges if e != edge)",
     "edges = model.edges", "Keep a deleted edge in the operated finite model."),
    ("honest_prefix_excision_preserved", "if vertex == endpoint:",
     "if vertex == END:", "Ignore the independently declared prefix endpoint."),
    ("posterior_uses_declared_prior",
     "posterior = [float(weights[m] / mass) for m in fibre]",
     "posterior = [1.0 / len(fibre) for m in fibre]",
     "Replace a declared unequal prior with a uniform one."),
    ("reconstruction_on_whole_class", "return inverse[observed]",
     "return next(iter(inverse.values()))",
     "Return one favourite completion for all distinguishable observations."),
    ("zero_prior_refused", "set(weights) == set(omega) and all(w > 0 for w in weights.values())",
     "set(weights) == set(omega)", "Allow zero prior weight to erase an admissible completion."),
    ("mean_binding_is_prior_weighted",
     "float(sum((weights[m] for m in group), F(0)) / total)",
     "F(1, len(groups))", "Average fibre entropies without their prior mass."),
    ("REFUSE:teeth_count", 'check("zero_prior_refused", prior_rejected)',
     "pass", "Delete one named check; the executed count must refuse."),
    ("SURVIVE:declaration_order", "START = 0\nEND = 4",
     "END = 4\nSTART = 0", "Reorder pure literal assignments without changing the finite audit."),
    ("REACH:declaration_order", "START = 0\nEND = 4",
     "START = 2\nEND = 4", "Change the declared start vertex used by the live reachability function."),
]


def load_copy(text, path, optimization=-1):
    path.write_text(text, encoding="utf-8")
    name = "_severance_local_copy"
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(text, str(path), "exec", optimize=optimization), module.__dict__)
    return module


def run(module, data):
    out = io.StringIO()
    crashed = False
    with redirect_stdout(out):
        try:
            alive = module.teeth(data)
        except Exception as exc:
            crashed = True
            alive = False
            print("CRASH " + type(exc).__name__ + ": " + str(exc))
    text = out.getvalue()
    reds = [line[5:] for line in text.splitlines() if line.startswith("FAIL ")]
    return {"ok": alive, "reds": reds, "stdout": text, "crashed": crashed, "start": module.START, "end": module.END}


def accepted(expected, outcome, first, equivalent):
    """Decide one copied case; a named failure counts only from a run that finished."""
    if expected == "SURVIVE":
        return bool(outcome["ok"] and not outcome["reds"] and not outcome["crashed"]
                    and outcome["start"] == 0 and outcome["end"] == 4 and equivalent)
    if expected == "REACH":
        return not outcome["crashed"] and first == "model_edge_loss_despite_observation_admit"
    if expected == "REFUSE":
        return outcome["crashed"] and "TEETH_COUNT" in outcome["stdout"]
    return not outcome["crashed"] and first == expected


def worker():
    """Run every copied mutation once, in this interpreter's own mode."""
    if sys.flags.optimize not in (0, 1):
        print("FAIL MODE")
        return 2
    mode = "-O" if sys.flags.optimize == 1 else "normal"
    source_bytes = SUBJECT.read_bytes()
    source = SUBJECT.read_text(encoding="utf-8")
    names = {node.args[0].value for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "check" and node.args
             and isinstance(node.args[0], ast.Constant)}
    targeted = {name for name, _, _, _ in BREAKS if ":" not in name}
    if names != targeted or EXPECTED_BREAKS != 14 or len(BREAKS) != 14 or len(targeted) != 11:
        print("FAIL MUTATION_CONTRACT")
        return 1
    rows = []
    with tempfile.TemporaryDirectory(prefix="copy-", dir=SUBJECT.parent) as temporary:
        copy = Path(temporary) / SUBJECT.name
        original = load_copy(source, copy)
        data = original.fixture(SUBJECT.parent)
        baseline = run(original, data)
        if not baseline["ok"]:
            raise RuntimeError(baseline["stdout"])
        print(baseline["stdout"], end="")
        for name, anchor, replacement, why in BREAKS:
            if source.count(anchor) != 1:
                raise RuntimeError("Mutation anchor is not unique: " + name)
            outcome = run(load_copy(source.replace(anchor, replacement, 1), copy), data)
            expected = "SURVIVE" if name.startswith("SURVIVE:") else (
                       "REACH" if name.startswith("REACH:") else (
                       "REFUSE" if name.startswith("REFUSE:") else name))
            first = outcome["reds"][0] if outcome["reds"] else ("CRASH" if outcome["crashed"] else None)
            equivalent = (anchor == "START = 0\nEND = 4"
                          and replacement == "END = 4\nSTART = 0"
                          and original.START == 0 and original.END == 4)
            ok = accepted(expected, outcome, first, equivalent)
            rows.append({"name": name, "ok": ok})
            print(("ok " if ok else "FAIL ") + name + " -> " + str(first))
    if SUBJECT.read_bytes() != source_bytes:
        print("FAIL SOURCE_UNCHANGED")
        return 1
    failures = [r["name"] for r in rows if not r["ok"]]
    print("mutations: %d/%d (%s)" % (len(rows) - len(failures), EXPECTED_BREAKS, mode))
    return 0 if not failures and len(rows) == EXPECTED_BREAKS else 1


def main(argv=None):
    """Run the worker once in normal Python and once in a separate -O interpreter."""
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--worker"]:
        return worker()
    if argv:
        print("USAGE: break_severance_stitch.py")
        return 2
    env = dict(os.environ)
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    statuses = []
    for optimize in (False, True):
        command = [sys.executable, "-B"] + (["-O"] if optimize else [])
        command += [str(Path(__file__).resolve()), "--worker"]
        completed = subprocess.run(command, env=env, capture_output=True, text=True)
        print(completed.stdout, end="", flush=True)
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr, flush=True)
        statuses.append(completed.returncode)
    if statuses == [0, 0]:
        print("SEVERANCE_MUTATIONS: PASS (%d/%d normal; %d/%d -O)" % ((EXPECTED_BREAKS,) * 4), flush=True)
        return 0
    return 1 if all(code in (0, 1) for code in statuses) else 2



if __name__ == "__main__":
    sys.exit(main())