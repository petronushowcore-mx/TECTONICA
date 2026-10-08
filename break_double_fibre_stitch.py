"""Eleven in-memory model changes and controls for eight Double Fibre checks."""
import ast
import json
from pathlib import Path
import sys
from types import ModuleType
import test_double_fibre_stitch as battery

HERE = Path(__file__).resolve().parent
MUTATIONS = (
    ('pin_missing_allowed', 'PIN_INVENTORY', 'double_fibre_stitch.py', 'if "DoubleFibre" not in data.commits:', 'if False:'),
    ('compatible_selector_lost', 'DECLARED_DOMAIN', 'double_fibre_stitch.py', 'worlds = tuple((model, word, name) for word in histories for name in names)', 'worlds = tuple((model, word, name) for word in histories for name in names[:1])'),
    ('declared_model_forgotten', 'V_RETAINS_D', 'double_fibre_stitch.py', 'return model, declaration["rows"][word]["observations"][mode]', 'return "forgotten-D", declaration["rows"][word]["observations"][mode]'),
    ('selector_ignored', 'SELECTOR_TARGET', 'double_fibre_stitch.py', 'return declaration["rows"][word][selector]', 'return declaration["rows"][word]["uninterrupted"]'),
    ('fibre_filter_lost', 'FIBRE_MEMBERSHIP', 'double_fibre_stitch.py', 'df.double_fibre(worlds, obs, y)', 'tuple(worlds)'),
    ('sufficiency_forced', 'FACTORIZATION', 'double_fibre_stitch.py', 'df.factors_through(worlds, obs, value)', 'True'),
    ('insufficient_rejected', 'TRICHOTOMY', 'double_fibre_stitch.py', 'df.trichotomy(worlds, obs, value, y)', '"reject"'),
    ('refinement_target_forgotten', 'LEAST_REFINEMENT', 'double_fibre_stitch.py', 'refined = df.least_refinement(obs, value)', 'refined = lambda world: (obs(world), 0)'),
    ('pin_present_rejected', 'PIN_INVENTORY', 'double_fibre_stitch.py', 'if "DoubleFibre" not in data.commits:', 'if True:'),
    ('model_local_rename', 'SURVIVE', 'test_double_fibre_stitch.py', 'prepared_snapshot = snapshot.copy(); snapshot = prepared_snapshot', 'captured_model = snapshot.copy(); snapshot = captured_model'),
    ('model_prepare_site_reached', 'REACH', 'test_double_fibre_stitch.py', 'prepared_snapshot = snapshot.copy(); snapshot = prepared_snapshot', 'prepared_snapshot = {key: value for key, value in snapshot.items() if key != "D"}; snapshot = prepared_snapshot'),
)


EXPECTED_MUTATIONS = 11


def rename_equivalent(original, changed):
    """Compare syntax after normalising the one local-variable rename."""
    class Normalise(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id == "captured_model":
                node.id = "prepared_snapshot"
            return node
    return ast.dump(Normalise().visit(ast.parse(original))) == ast.dump(Normalise().visit(ast.parse(changed)))


def main():
    try:
        snapshot, df = battery.context()
    except (battery.production.tectonica.Refusal, OSError, ValueError, TypeError) as error:
        print("DOUBLE_FIBRE_BREAKS: REFUSED " + str(error), file=sys.stderr)
        return 2
    original_adapter = (HERE / "double_fibre_stitch.py").read_text(encoding="utf-8")
    baseline = battery.rows(battery.evaluate(original_adapter), snapshot, df)
    baseline_ok = (len(baseline) == 8 and tuple(row["name"] for row in baseline) == battery.NAMES
                   and all(row["ok"] for row in baseline))
    reports = []
    for label, marker, file, old, new in MUTATIONS:
        original = (HERE / file).read_text(encoding="utf-8")
        count = original.count(old)
        details = []
        first = "ANCHOR_CARDINALITY"
        parsed = False
        equivalent = None
        if count == 1:
            changed = original.replace(old, new, 1)
            try:
                if file == "test_double_fibre_stitch.py":
                    active = ModuleType("_df_battery_copy")
                    active.__file__ = str(HERE / file)
                    exec(compile(changed, active.__file__, "exec"), active.__dict__)
                    details = active.rows(battery.evaluate(original_adapter), snapshot, df)
                else:
                    details = battery.rows(battery.evaluate(changed), snapshot, df)
                parsed = True
                first = next((row["name"] for row in details if not row["ok"]), None)
                if marker == "SURVIVE":
                    equivalent = rename_equivalent(original, changed)
            except Exception as error:
                first = type(error).__name__ + ": " + str(error)
        alive = parsed and len(details) == 8 and tuple(row["name"] for row in details) == battery.NAMES
        if marker == "SURVIVE":
            okay = alive and first is None and equivalent is True
        elif marker == "REACH":
            okay = alive and first == "DECLARED_DOMAIN"
        else:
            okay = alive and first == marker
        reports.append({"name": label, "expected": marker, "first_red": first,
                        "ok": bool(okay), "parsed": parsed, "alive": bool(alive),
                        "anchor_count": count, "equivalence": equivalent, "checks": details})
        print(("PASS " if okay else "FAIL ") + label + " first=" + str(first) + " expected=" + marker)
    okay = baseline_ok and len(reports) == 11 and all(row["ok"] for row in reports)
    print(json.dumps({"baseline": baseline, "baseline_ok": baseline_ok,
                      "mutations": reports, "ok": okay}, indent=2))
    print("DOUBLE_FIBRE_BREAKS: " + ("PASS" if okay else "FAIL") + " (11 cases; 8 named checks)")
    return 0 if okay else 1


if __name__ == "__main__":
    raise SystemExit(main())

