"""Finite ordered recomposition routes interpreted by the pinned Person API.

Exact nonnegative rational charges and a fixed capacity; integer spans are
declared auxiliary coordinates. These reports do not certify physical time,
moral character, whole-system identity or execution of a rejected route.
"""
from fractions import Fraction as F
from pathlib import Path
import json
import sys

import identity_stitch
import pinned_sources
import person_adapter
import recomposition_stitch as recomposition
import tectonica

ROOT = Path(__file__).resolve().parent
EXPECTED_TEETH = 8


def require(condition, marker):
    if not condition:
        raise tectonica.Refusal(marker)


def load(selected):
    require("Person" in selected, "PIN_REQUIRED: Person")
    return pinned_sources._load(
        selected, "tectonica_person",
        Path(selected["Person"][0]) / "person_harness.py")


def fixture(root=ROOT):
    selected = tectonica.checked_layers(root)
    person = load(selected)
    data = recomposition.fixture(root)
    return dict(data, person=person,
                commits={name: revision for name, (_, revision) in selected.items()},
                person_source_sha256=person._xiv_stitch_source_sha256)


def rows(data):
    person = data["person"]
    original = data["graph"]
    _, fragment, boundary, folded, cheap, costly = recomposition.cases(data)
    original_path, fold_path, donor_path = (0, 1, 2, 3, 4), (0, 1, 3, 4), (0, 1, 5, 3, 4)
    varied = original._replace(edges=tuple(
        e._replace(cost=F(2, 3), trace=(recomposition.Window(F(2, 3), 1),))
        if e.source == 2 else e for e in original.edges))
    varied_fragment, varied_boundary = recomposition.cut(varied)
    varied_fold = recomposition.fold(varied_fragment, varied_boundary)
    branched = costly._replace(edges=costly.edges + (
        recomposition.Edge(0, 4, F(1, 4), 1, (recomposition.Window(F(1, 4), 1),)),))
    spanned = costly._replace(horizon=8, edges=tuple(e._replace(
        span=2, trace=tuple(w._replace(span=2) for w in e.trace))
        for e in costly.edges))

    def refused(operation, kind, text):
        try:
            operation()
        except kind as error:
            return str(error) == text
        return False

    def report(graph, path):
        return person_adapter.selected_report(graph, path, recomposition, person)

    checks = (
        ("ORDERED_WINDOWS", lambda:
         len(recomposition.edges_of(folded, fold_path)) == 3
         and tuple((w.cost, w.span) for w in person_adapter.project(
             varied_fold, fold_path, recomposition, person)) ==
             ((F(1, 3), 1), (F(1, 3), 1), (F(2, 3), 1), (F(1, 3), 1))),
        ("COMPLETE_PATH", lambda:
         refused(lambda: person_adapter.project(original, (0, 1), recomposition, person),
                 person_adapter.Refusal, "COMPLETE_SELECTED_ROUTE")
         and refused(lambda: person_adapter.project(fragment, original_path, recomposition, person),
                     person_adapter.Refusal, "COMPLETE_SELECTED_ROUTE")),
        ("SELECTED_NOT_EXISTENTIAL", lambda:
         recomposition.functional(branched) is True
         and report(branched, donor_path)["whole_survival"] is False
         and report(branched, (0, 4))["whole_survival"] is True),
        ("EXACT_PREFIX", lambda:
         report(costly, donor_path)["capacity"] == F(2)
         and report(costly, donor_path)["prefix_budgets"] ==
             ((F(5, 3), 1), (F(2, 3), 2), (F(-1, 3), 3), (F(-2, 3), 4))
         and all(type(budget) is F for budget, _ in
                 report(costly, donor_path)["prefix_budgets"])),
        ("FINAL_WHOLE", lambda:
         all(report(graph, path)["final_survival"] is expected
             and report(graph, path)["whole_survival"] is expected
             for graph, path, expected in
             ((original, original_path, True), (folded, fold_path, True),
              (cheap, donor_path, True), (costly, donor_path, False),
              (cheap._replace(capacity=F(1)), donor_path, False)))),
        ("CROSSING_PAIR", lambda:
         report(costly, donor_path)["first_crossing"] == (3, 3)
         and report(spanned, donor_path)["first_crossing"] == (3, 6)
         and report(varied_fold._replace(capacity=F(1)), fold_path)["first_crossing"] == (3, 3)
         and report(folded, fold_path)["first_crossing"] is None),
        ("FIXED_CAPACITY", lambda:
         refused(lambda: person_adapter.compare(original, original_path,
                 costly._replace(capacity=F(3)), donor_path, recomposition, person),
                 person_adapter.Refusal, "FIXED_CAPACITY_CONTEXT")),
        ("ADMISSIBLE_BASELINE", lambda:
         refused(lambda: person_adapter.compare(costly, donor_path, cheap, donor_path,
                 recomposition, person), person.Refusal, "loss requires an admissible baseline")
         and person_adapter.compare(original, original_path, costly, donor_path,
                                     recomposition, person) == "lost"
         and person_adapter.compare(original, original_path, cheap, donor_path,
                                     recomposition, person) == "preserved"),
    )
    result = []
    for name, operation in checks:
        try:
            passed = operation() is True
            detail = "" if passed else "predicate was not true"
        except Exception as error:
            passed, detail = False, type(error).__name__ + ": " + str(error)
        result.append({"name": name, "ok": passed, "detail": detail})
    require(len(result) == EXPECTED_TEETH == 8 and len({r["name"] for r in result}) == 8,
            "TEETH_COUNT")
    return result


def result(data):
    person = data["person"]
    original, cut, boundary, folded, cheap, costly = recomposition.cases(data)
    cases = {}
    for name, graph in (("original", original), ("cut", cut), ("fold", folded),
                        ("cheap", cheap), ("costly", costly)):
        cases[name] = {"complete_routes": [
            dict(person_adapter.selected_report(graph, path, recomposition, person), path=path)
            for path, _, _ in recomposition.routes(graph)]}
    return {"scope": "Finite proposed complete routes; fixed capacity and declared window coordinates.",
            "commits": data["commits"],
            "person_source_sha256": data["person_source_sha256"],
            "source_provenance": data["source_provenance"],
            "cases": cases,
            "final_whole_equivalence": "Fixed capacity and nonnegative charges make prefix budgets nonincreasing.",
            "whole_system_identity": "not_established"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        require(argv in ([], ["--teeth"]), "USAGE: person_stitch.py [--teeth]")
        data = fixture()
        checked = rows(data)
        for row in checked:
            print(("PASS " if row["ok"] else "FAIL ") + row["name"]
                  + (": " + row["detail"] if row["detail"] else ""))
        print("teeth: %d/%d" % (sum(row["ok"] for row in checked), EXPECTED_TEETH))
        if not all(row["ok"] for row in checked):
            return 1
        if not argv:
            print(json.dumps(result(data), indent=2, default=str))
        print("PERSON_CONNECTION: PASS (finite selected-route interpretation)")
        return 0
    except (tectonica.Refusal, recomposition.Refusal, identity_stitch.Refusal,
            person_adapter.Refusal, OSError, ValueError) as error:
        print("PERSON_CONNECTION: REFUSED " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
