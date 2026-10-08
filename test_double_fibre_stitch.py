"""Eight named checks on the installed PoA27 and Double Fibre connection."""
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
import double_fibre_stitch as production

HERE = Path(__file__).resolve().parent
EXPECTED_CHECKS = 8
NAMES = ("PIN_INVENTORY", "DECLARED_DOMAIN", "V_RETAINS_D", "SELECTOR_TARGET",
         "FIBRE_MEMBERSHIP", "FACTORIZATION", "TRICHOTOMY", "LEAST_REFINEMENT")


def context():
    """Load verified installed source buffers and capture their current PoA27."""
    data = production.load_sources(HERE)
    return production.capture(data), data.double_fibre


def evaluate(body):
    module = ModuleType("_df_adapter_copy")
    module.__file__ = str(HERE / "double_fibre_stitch.py")
    exec(compile(body, module.__file__, "exec"), module.__dict__)
    return module


def rows(app, snapshot, df):
    prepared_snapshot = snapshot.copy(); snapshot = prepared_snapshot
    results = []
    def check(name, predicate):
        try:
            okay = bool(predicate())
            results.append({"name": name, "ok": okay})
        except Exception as exc:
            results.append({"name": name, "ok": False, "detail": type(exc).__name__ + ": " + str(exc)})
    def pin_inventory():
        absent = SimpleNamespace(commits=dict(snapshot["commits"]))
        absent.commits.pop("DoubleFibre", None)
        try:
            app.require_df_pin(absent)
        except app.tectonica.Refusal:
            pass
        else:
            return False
        present = SimpleNamespace(commits=dict(snapshot["commits"]))
        app.require_df_pin(present)
        return True
    def declarations():
        expected_words = {a+b+c for a in "ABC" for b in "ABC" for c in "ABC"}
        for names in (("uninterrupted",), ("uninterrupted", "composite")):
            dec = app.declare(snapshot, names)
            expected = {(snapshot["D"], word, name) for word in expected_words for name in names}
            if len(dec["worlds"]) != len(expected) or set(dec["worlds"]) != expected:
                return False
        return True
    def retained():
        dec = app.declare(snapshot)
        for world in dec["worlds"]:
            for mode in app.poa.OBSERVATIONS:
                if app.visible(dec, world, mode) != (world[0], snapshot["rows"][world[1]]["observations"][mode]):
                    return False
        return True
    def selected():
        dec = app.declare(snapshot, ("uninterrupted", "composite"))
        values = [app.target(dec, world) for world in dec["worlds"]]
        differences = {word for word, row in snapshot["rows"].items() if row["uninterrupted"] != row["composite"]}
        return differences == {"ACC", "BCC", "CCA", "CCB"} and all(
            type(value) is int and value == snapshot["rows"][world[1]][world[2]]
            for world, value in zip(dec["worlds"], values))
    def audits():
        for names in (("uninterrupted",), ("uninterrupted", "composite")):
            dec = app.declare(snapshot, names)
            for mode in app.poa.OBSERVATIONS:
                yield dec, mode, app.audit(dec, df, mode)
    def oracle_visible(world, mode):
        return world[0], snapshot["rows"][world[1]]["observations"][mode]
    def oracle_target(world):
        return snapshot["rows"][world[1]][world[2]]
    def fibres():
        for dec, mode, report in audits():
            groups = {}
            for world in dec["worlds"]:
                groups.setdefault(oracle_visible(world, mode), []).append(world)
            if {r["visible"]: tuple(r["worlds"]) for r in report["fibres"]} != {k:tuple(v) for k,v in groups.items()}:
                return False
        return True
    def factorization():
        for dec, mode, report in audits():
            expected = all(oracle_visible(a, mode) != oracle_visible(b, mode)
                           or oracle_target(a) == oracle_target(b)
                           for a in dec["worlds"] for b in dec["worlds"])
            if report["factors_through"] != expected:
                return False
        return True
    def trichotomy():
        seen = set()
        for dec, mode, report in audits():
            for fibre in report["fibres"]:
                values = {oracle_target(world) for world in dec["worlds"]
                          if oracle_visible(world, mode) == fibre["visible"]}
                expected = "admit" if values == {1} else "reject" if values == {0} else "insufficient observation"
                if fibre["verdict"] != expected:
                    return False
                seen.add(expected)
            for first, second in report["selector_only_witnesses"]:
                if not (first[0:2] == second[0:2] and first[2] != second[2]
                        and oracle_visible(first, mode) == oracle_visible(second, mode)
                        and oracle_target(first) != oracle_target(second)):
                    return False
            if len(dec["selectors"]) == 2 and {a[1] for a,b in report["selector_only_witnesses"]} != {"ACC", "BCC", "CCA", "CCB"}:
                return False
        return seen == {"admit", "reject", "insufficient observation"}
    def refinement():
        for dec, mode, report in audits():
            expected = tuple((oracle_visible(w, mode), oracle_target(w)) for w in dec["worlds"])
            if report["least_refinement"] != expected or not report["refined_factors_through"]:
                return False
        return True
    check("PIN_INVENTORY", pin_inventory)
    check("DECLARED_DOMAIN", declarations)
    check("V_RETAINS_D", retained)
    check("SELECTOR_TARGET", selected)
    check("FIBRE_MEMBERSHIP", fibres)
    check("FACTORIZATION", factorization)
    check("TRICHOTOMY", trichotomy)
    check("LEAST_REFINEMENT", refinement)
    return results


class DoubleFibreTests(unittest.TestCase):
    """Two unittest cases cover the count and all eight named predicates."""
    @classmethod
    def setUpClass(cls):
        snapshot, df = context()
        cls.results = rows(production, snapshot, df)

    def test_named_check_count(self):
        self.assertEqual(len(self.results), 8, "DOUBLE_FIBRE_CHECK_COUNT")
        self.assertEqual(tuple(row["name"] for row in self.results), NAMES,
                         "DOUBLE_FIBRE_CHECK_NAMES")

    def test_named_checks(self):
        for row in self.results:
            with self.subTest(name=row["name"]):
                self.assertTrue(row["ok"], row["name"] + ": " + row.get("detail", ""))


def main():
    try:
        snapshot, df = context()
        result = rows(production, snapshot, df)
    except (production.tectonica.Refusal, OSError, ValueError, TypeError) as error:
        print("DOUBLE_FIBRE_CHECKS: REFUSED " + str(error), file=sys.stderr)
        return 2
    for row in result:
        print(("PASS " if row["ok"] else "FAIL ") + row["name"] + " " + row.get("detail", ""))
    okay = len(result) == 8 and tuple(row["name"] for row in result) == NAMES and all(row["ok"] for row in result)
    print("DOUBLE_FIBRE_CHECKS: " + ("PASS" if okay else "FAIL") + " (8 named checks)")
    return 0 if okay else 1


if __name__ == "__main__":
    raise SystemExit(main())

