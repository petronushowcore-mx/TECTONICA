"""Run the copied mutations and controls against the finite recomposition adapter.

Usage: python -B break_recomposition_stitch.py [REPO_ROOT]

REPO_ROOT defaults to this file's directory. It must contain recomposition_stitch.py,
its root adapters, and the five initialized, clean, pinned TECTONICA dependencies.
Both normal and -O execution are tested. Only temporary model copies are changed.
The runner's directory must be writable. Run only trusted source and dependencies.
Mutation anchors describe this adapter version; a changed anchor is refused.
These finite examples do not establish arbitrary graph composition or identity.
"""
import argparse
import ast
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types

EXPECTED_CHECKS = 16

BREAKS = [
    ("actual_source_burden", "cost + edge.cost", "cost", "Discard actual path burden."),
    ("excision_breaks_route", "return fragment, Boundary(", "return graph, Boundary(",
     "Return uncut graph as the cut fragment."),
    ("excision_breaks_route", "require(incident == declared,", "require(True,",
     "Ignore undeclared contacts of the removed component."),
    ("fold_preserves_burden",
     "trace = boundary.trace",
     "trace = tuple(Window(w.cost / 2, w.span) for w in boundary.trace)",
     "Erase half the removed burden while rebuilding internally consistent trace metadata."),
    ("fold_preserves_declared_span",
     "trace = boundary.trace",
     "trace = (Window(sum((w.cost for w in boundary.trace), F(0)), 1),)",
     "Erase one declared window of the folded component."),
    ("donor_changes_pattern", "return validate(fragment._replace(vertices=vertices, edges=edges))",
     "return fold(fragment, boundary)", "Discard replacement component and silently use a fold."),
    ("reachable_route_can_exhaust_budget",
     "return any(cost < graph.capacity for _, cost, _ in routes(graph))",
     "return bool(routes(graph))", "Conflate endpoint reachability with budget survival."),
    ("port_contract_rejects",
     'require(boundary.outgoing.polarity == "out" and boundary.incoming.polarity == "in"\n'
     '            and boundary.outgoing.payload == boundary.incoming.payload, "BOUNDARY_PORTS")',
     'require(True, "BOUNDARY_PORTS")', "Accept mismatched boundary port type or direction."),
    ("port_contract_rejects",
     'require(part.entry.polarity == "in" and part.exit.polarity == "out"\n'
     '                and part.entry.payload == boundary.outgoing.payload\n'
     '                and part.exit.payload == boundary.incoming.payload, "DONOR_PORTS")',
     'require(True, "DONOR_PORTS")', "Accept donor type or direction mismatch."),
    ("attachment_mapping_rejects", "require(set(mapping) == set(part.vertices),",
     "require(True,", "Allow incomplete donor map."),
    ("attachment_mapping_rejects", "require(len(set(mapping.values())) == len(mapping),",
     "require(True,", "Allow a non-injective donor map."),
    ("attachment_mapping_rejects",
     'require(mapping[part.entry.vertex] == boundary.outgoing.vertex\n'
     '            and mapping[part.exit.vertex] == boundary.incoming.vertex, "MAPPED_PORTS")',
     'require(True, "MAPPED_PORTS")', "Attach donor endpoints to undeclared ports."),
    ("attachment_mapping_rejects", "require(all(mapping[v] not in fragment.vertices for v in internal),",
     "require(True,", "Reuse an exterior vertex as donor interior."),
    ("observation_preserved_loss_unknown",
     "graph.start, graph.goal, graph.horizon, graph.capacity)",
     "graph.start, graph.goal, graph.horizon, graph.capacity, graph.edges)",
     "Leak full hidden weights into the declared shape observation."),
    ("real_xiv_xv_ie", "{i: e.cost for i, e in enumerate(graph.edges)}",
     "{i: F(0) for i, e in enumerate(graph.edges)}", "Erase weights at the actual XV import boundary."),
    ("route_loss_not_global_non_nestability",
     'return data["base"].api.nest.is_nestable(to_xv(graph, data))',
     "return functional(graph)", "Replace global XV criterion with a selected-route decision."),
    ("declared_horizon_enforced", "next_span <= graph.horizon", "True",
     "Ignore the declared span bound."),
    ("strict_budget_boundary", "cost < graph.capacity for _, cost, _ in routes(graph)",
     "cost <= graph.capacity for _, cost, _ in routes(graph)", "Accept exact budget exhaustion."),
    ("trajectory_order_not_aggregate", "trace = boundary.trace",
     "trace = tuple(reversed(boundary.trace))", "Reverse ordered internal windows while preserving totals."),
    ("trajectory_order_not_aggregate", "return elapsed", "return sum(w.span for w in trace)",
     "Report the final window instead of first crossing."),
    ("report_trace_is_derived", 'Counter(\n                trace_of(original, path) for path, _, _ in routes(original)) == Counter(\n                trace_of(folded, path) for path, _, _ in routes(folded))', "True",
     "Report success despite reversed nonuniform windows."),
    ("report_trace_is_derived", 'Counter(\n                trace_of(original, path) for path, _, _ in routes(original)) == Counter(\n                trace_of(folded, path) for path, _, _ in routes(folded))', "False",
     "Report failure for an honest fold or changed enumeration order."),
    ("SURVIVE:declaration_order", "ZERO = 0\nONE = 1", "ONE = 1\nZERO = 0",
     "Reorder independent literal assignments."),
    ("REACH:declaration_order", "ZERO = 0\nONE = 1", "ZERO = 1\nONE = 1",
     "Corrupt the initial route cost."),
    ("REFUSE:teeth_count",
     'check("strict_budget_boundary", not functional(original._replace(capacity=F(4, 3))))',
     "pass", "Delete one named check; the executed count must refuse."),
]

# Each invalid-graph guard has a copied removal and a corresponding invalid model.
GUARDS = [
    'require(bool(graph.vertices) and len(set(graph.vertices)) == len(graph.vertices),\n'
    '            "VERTEX_SET")',
    'require(graph.start in graph.vertices and graph.goal in graph.vertices\n'
    '            and graph.start != graph.goal, "ENDPOINTS")',
    'require(isinstance(graph.capacity, F) and graph.capacity > 0, "CAPACITY")',
    'require(type(graph.horizon) is int and graph.horizon > 0, "HORIZON")',
    'require(len(set(pairs)) == len(pairs), "UNIQUE_EDGES")',
    'require(e.source in graph.vertices and e.target in graph.vertices, "EDGE_ENDPOINT")',
    'require(isinstance(e.cost, F) and e.cost >= 0, "EXACT_NONNEGATIVE_COST")',
    'require(type(e.span) is int and e.span > 0, "POSITIVE_SPAN")',
    'require(bool(e.trace) and all(isinstance(w.cost, F) and w.cost >= 0\n'
    '                and type(w.span) is int and w.span > 0 for w in e.trace)\n'
    '                and sum((w.cost for w in e.trace), F(0)) == e.cost\n'
    '                and sum(w.span for w in e.trace) == e.span, "TRACE_ACCOUNTING")',
]
BREAKS += [("graph_contract_refuses_invalid", anchor,
            'require(True, ' + repr(anchor.rsplit('"', 2)[1]) + ')',
            "Remove the named invalid-graph guard.") for anchor in GUARDS]
EXPECTED_BREAKS = 34

def check_names(source):
    calls = [node.args[0].value for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "check" and node.args
             and isinstance(node.args[0], ast.Constant)
             and isinstance(node.args[0].value, str)]
    targeted = {name for name, _, _, _ in BREAKS if ":" not in name}
    if (len(BREAKS) != EXPECTED_BREAKS or len(calls) != EXPECTED_CHECKS
            or len(set(calls)) != EXPECTED_CHECKS or set(calls) != targeted):
        raise RuntimeError("Mutation count or named check coverage differs.")
    for name, anchor, _, _ in BREAKS:
        if source.count(anchor) != 1:
            raise RuntimeError("Mutation anchor is not unique: " + name)
    return set(calls)


def literal_reorder_equivalent(before, after):
    """Prove only a permutation of independent, distinct literal assignments."""
    def assignments(text):
        values = {}
        for node in ast.parse(text).body:
            if (not isinstance(node, ast.Assign) or len(node.targets) != 1
                    or not isinstance(node.targets[0], ast.Name)
                    or not isinstance(node.value, ast.Constant)
                    or node.targets[0].id in values):
                return None
            values[node.targets[0].id] = ast.dump(node.value)
        return values or None
    left, right = assignments(before), assignments(after)
    return left is not None and right is not None and left == right


def load_copy(source, path, name):
    path.write_text(source, encoding="utf-8")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def run_model(module, data):
    output = io.StringIO()
    crashed = False
    with redirect_stdout(output):
        try:
            ok = module.teeth(data)
        except Exception as exc:
            ok, crashed = False, True
            print("CRASH " + type(exc).__name__ + ": " + str(exc))
    text = output.getvalue()
    reds = [line[5:] for line in text.splitlines() if line.startswith("FAIL ")]
    passes = [line[3:] for line in text.splitlines() if line.startswith("ok ")]
    return {"ok": ok is True, "crashed": crashed, "reds": reds,
            "passes": passes, "stdout": text}


def green(outcome, names):
    return (outcome["ok"] and not outcome["crashed"] and not outcome["reds"]
            and len(outcome["passes"]) == EXPECTED_CHECKS
            and set(outcome["passes"]) == names)


def accepted_case(name, outcome, anchor, replacement, names):
    first = outcome["reds"][0] if outcome["reds"] else None
    if name.startswith("SURVIVE:"):
        return green(outcome, names) and literal_reorder_equivalent(anchor, replacement)
    if name.startswith("REACH:"):
        return not outcome["crashed"] and first == "actual_source_burden"
    if name.startswith("REFUSE:"):
        return outcome["crashed"] and "TEETH_COUNT" in outcome["stdout"]
    return not outcome["crashed"] and first == name


def worker(root):
    source_path = root / "recomposition_stitch.py"
    original_bytes = source_path.read_bytes()
    source = source_path.read_text(encoding="utf-8")
    names = check_names(source)
    sys.path.insert(0, str(root))
    mode = "-O" if sys.flags.optimize == 1 else "normal"
    if sys.flags.optimize not in (0, 1):
        raise RuntimeError("Only normal and -O execution are declared.")
    failed = []
    with tempfile.TemporaryDirectory(prefix="recomposition-copy-",
                                     dir=Path(__file__).resolve().parent) as temporary:
        copy = Path(temporary) / source_path.name
        original = load_copy(source, copy, "_recomposition_baseline")
        data = original.fixture(root)
        baseline = run_model(original, data)
        if not green(baseline, names):
            raise RuntimeError("Baseline did not pass all named checks:\n" + baseline["stdout"])
        print("baseline: %d/%d (%s)" % (len(baseline["passes"]), EXPECTED_CHECKS, mode), flush=True)
        for index, (name, anchor, replacement, reason) in enumerate(BREAKS):
            changed = source.replace(anchor, replacement, 1)
            try:
                module = load_copy(changed, copy, "_recomposition_case_" + str(index))
                outcome = run_model(module, data)
            except Exception as exc:
                outcome = {"ok": False, "crashed": True, "reds": [], "passes": [],
                           "stdout": "CRASH " + type(exc).__name__ + ": " + str(exc)}
            ok = accepted_case(name, outcome, anchor, replacement, names)
            first = outcome["reds"][0] if outcome["reds"] else (
                    "CRASH" if outcome["crashed"] else "none")
            print(("ok " if ok else "FAIL ") + str(index + 1) + " " + name
                  + " -> " + first, flush=True)
            if not ok:
                failed.append(index + 1)
                print(reason + "\n" + outcome["stdout"], flush=True)
    if source_path.read_bytes() != original_bytes:
        raise RuntimeError("Selected source changed during copied mutations.")
    print("mutations: %d/%d (%s)" % (EXPECTED_BREAKS - len(failed), EXPECTED_BREAKS, mode),
          flush=True)
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    try:
        if args.worker:
            return worker(root)
        statuses = []
        env = dict(os.environ)
        env.pop("PYTHONOPTIMIZE", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for optimize in (False, True):
            command = [sys.executable, "-B"]
            if optimize:
                command.append("-O")
            command += [str(Path(__file__).resolve()), "--worker", str(root)]
            completed = subprocess.run(command, env=env, capture_output=True, text=True)
            print(completed.stdout, end="", flush=True)
            if completed.stderr:
                print(completed.stderr, end="", file=sys.stderr, flush=True)
            statuses.append(completed.returncode)
        if statuses == [0, 0]:
            print("RECOMPOSITION_MUTATIONS: PASS (%d/%d normal; %d/%d -O)"
                  % ((EXPECTED_BREAKS,) * 4), flush=True)
            return 0
        return 1 if all(code in (0, 1) for code in statuses) else 2
    except Exception as exc:
        print("ERROR " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
