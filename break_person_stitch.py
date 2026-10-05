"""Mutate adapter buffers, leaving all pinned sources unchanged."""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

import person_stitch as app
import tectonica

ROOT = Path(__file__).resolve().parent
EXPECTED_BREAKS = 12
MUTATIONS = (
    ("ORDERED_WINDOWS", "recomposition.trace_of(graph, path)",
     "tuple(reversed(recomposition.trace_of(graph, path)))"),
    ("ORDERED_WINDOWS", "for w in recomposition.trace_of(graph, path)",
     "for w in recomposition.edges_of(graph, path)"),
    ("COMPLETE_PATH", "if type(path) is not tuple or path not in tuple(p for p, _, _ in recomposition.routes(graph)):",
     "if False:"),
    ("SELECTED_NOT_EXISTENTIAL", "person.whole_survival(trace, graph.capacity)",
     "recomposition.functional(graph)"),
    ("EXACT_PREFIX", "person.prefix_budgets(trace, graph.capacity)",
     "person.prefix_budgets(trace, graph.capacity + 1)"),
    ("EXACT_PREFIX", "person.prefix_budgets(trace, graph.capacity)",
     "person.prefix_budgets(trace, graph.capacity)[-1:]"),
    ("EXACT_PREFIX", '"capacity": graph.capacity', '"capacity": graph.capacity + 1'),
    ("FINAL_WHOLE", "person.final_survival(trace, graph.capacity)",
     "person.prefix_budgets(trace, graph.capacity)[0][0] > 0"),
    ("FINAL_WHOLE", "person.whole_survival(trace, graph.capacity)",
     "all(b > 0 for b, _ in person.prefix_budgets(trace, graph.capacity)[:-1])"),
    ("CROSSING_PAIR", "person.first_crossing(trace, graph.capacity)",
     "recomposition.first_crossing(trace, graph.capacity)"),
    ("FIXED_CAPACITY", "if before.capacity != after.capacity:", "if False:"),
    ("ADMISSIBLE_BASELINE", "return person.loss_status(old, new, before.capacity)",
     'return "preserved" if person.final_survival(new, before.capacity) else "lost"'),
)


def require(value, marker):
    if not value:
        raise RuntimeError(marker)


def evaluate(body):
    module = ModuleType("_person_adapter_copy")
    exec(compile(body, "person_adapter_copy", "exec"), module.__dict__)
    return module


def run(data=None):
    data = app.fixture(tectonica.ROOT) if data is None else data
    source = (ROOT / "person_adapter.py").read_text(encoding="utf-8-sig")
    require(len(MUTATIONS) == EXPECTED_BREAKS == 12, "MUTATION_COUNT")
    healthy = app.rows(data)
    require(all(r["ok"] for r in healthy), "BASELINE_FAILURE")
    order = [r["name"] for r in healthy]
    reached = set()
    for number, (expected, old, new) in enumerate(MUTATIONS, 1):
        require(source.count(old) == 1, "MUTATION_ANCHOR_%d" % number)
        with patch.object(app, "person_adapter", evaluate(source.replace(old, new))):
            result = app.rows(data)
        require([r["name"] for r in result] == order, "MUTATION_VERDICT_ORDER")
        reds = [r["name"] for r in result if not r["ok"]]
        require(bool(reds) and reds[0] == expected, "FIRST_RED_%d: %r" % (number, reds))
        reached.add(expected)
        print("BREAK %02d first_red=%s" % (number, expected))
    require(reached == set(order), "UNCOVERED_NAMED_CHECK")
    # Equivalent changes survive; a correct negative verdict still computes.
    with patch.object(app, "person_adapter", evaluate(source.replace(
            "person.Window(w.cost, w.span)", "person.Window(w.cost + 0, w.span)"))):
        require(all(r["ok"] for r in app.rows(data)), "EQUIVALENT_CHANGE_REFUSED")
    with patch.object(app, "fixture", return_value=data), redirect_stdout(io.StringIO()):
        require(app.main(["--teeth"]) == 0, "SCIENTIFIC_REJECT_OVERFIRED")
    with patch.object(app, "fixture", side_effect=tectonica.Refusal("PIN_REQUIRED: Person")), \
         redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as error:
        require(app.main([]) == 2 and "REFUSED PIN_REQUIRED: Person" in error.getvalue(),
                "CHILD_REFUSAL_NOT_PROPAGATED")
    print("controls: equivalent change survives; scientific rejection computes; missing pin refuses")
    print("breaks: %d/%d; checks covered: %d/%d" %
          (EXPECTED_BREAKS, EXPECTED_BREAKS, len(reached), app.EXPECTED_TEETH))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(run())
