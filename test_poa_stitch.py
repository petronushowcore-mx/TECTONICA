"""Exact finite bridge tests using the pinned dependencies."""
import copy
import hashlib
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import identity_stitch as identity
import poa_stitch as poa
import pinned_sources
from test_pinned_sources import fixture_git


class PoATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = poa.load_sources(Path(__file__).resolve().parent)
        cls.maps, cls.eta, cls.gamma = identity.certified_model(cls.data)
        cls.result = poa.run(cls.data)
        cls.rows = cls.result["histories"]

    def test_catalogue_and_accounting(self):
        expected = {"".join(w) for w in product("ABC", repeat=3)}
        self.assertEqual(set(self.rows), expected, "P_CATALOGUE")
        for row in self.rows.values():
            self.assertEqual(row["cumulative_costs"], ["1/3", "2/3", "1", "4/3"], "P_COSTS")
            self.assertEqual(row["accounting_prefix_burdens"], row["cumulative_costs"], "P_ACCOUNTING")
            self.assertEqual(row["ie"]["verdict"], "NESTED-BOUNDARY", "P_IE")
        with self.assertRaisesRegex(identity.Refusal, "^POA_CATALOGUE_WORD$"):
            poa.history_record(self.data, "AB")

    def test_full_covector(self):
        for name, expected in [("A", (1, 0)), ("B", (1, 0)), ("C", (0, 1))]:
            self.assertEqual(poa.covector_pullback(self.data, self.maps[name]), expected, "P_PULLBACK_" + name)
        extra = {0: [(0, 1)], 1: [(0, 1), (1, 1)]}
        self.assertEqual(poa.covector_pullback(self.data, extra), (1, 1), "P_SECOND_BASIS")
        self.assertFalse(poa.membership(self.data, extra), "P_WHOLE_COVECTOR")

    def test_total_graph_map(self):
        bad = copy.deepcopy(self.maps["B"])
        del bad[1]
        with self.assertRaisesRegex(identity.Refusal, "^POA_GRAPH_MAP:"):
            poa.covector_pullback(self.data, bad)
        self.assertTrue(poa.membership(self.data, self.maps["B"]), "P_TOTAL_POSITIVE")

    def test_path_backtracking(self):
        same = copy.deepcopy(self.maps["B"])
        same[0] += [(1, 1), (1, -1)]
        self.assertEqual(poa.covector_pullback(self.data, same), (1, 0), "P_PATH_SEMANTICS")
        self.assertTrue(poa.membership(self.data, same), "P_BACKTRACK_POSITIVE")

    def test_membership_and_composite(self):
        expected = {
            "BAA": ([True, True, True], True, True, ["1", "0"]),
            "BCC": ([True, False, False], False, True, ["1", "0"]),
            "BBA": ([True, True, True], True, True, ["1", "0"]),
            "BBC": ([True, True, False], False, False, ["2", "1"]),
        }
        for word, values in expected.items():
            row = self.rows[word]
            self.assertEqual(tuple(row[k] for k in (
                "P_eta_membership", "P_eta_uninterrupted", "P_eta_composite_admitted",
                "composite_covector_pullback")), values, "P_HISTORY_" + word)
        self.assertEqual(self.rows["BCC"]["periods"], ["1", "1", "0", "1"], "P_RETURN")
        self.assertEqual(self.rows["BBA"]["periods"], ["1", "1", "1", "1"], "P_CONSTANT")
        self.assertEqual(self.rows["BBC"]["periods"], ["1", "1", "1", "1"], "P_CONSTANT_LOSS")

    def test_same_composite_different_history(self):
        def composite(word):
            result = {0: [(0, 1)], 1: [(1, 1)]}
            for event in word:
                result = identity.compose(result, self.maps[event])
            return result
        self.assertEqual(composite("BAA"), self.maps["B"], "P_BAA_MAP")
        self.assertEqual(composite("BCC"), self.maps["B"], "P_BCC_MAP")
        self.assertEqual(self.rows["BAA"]["cycles"][-1], self.rows["BCC"]["cycles"][-1], "P_ENDPOINT")

    def test_observation_separations(self):
        for mode, pair in [("final_cycle_cost", ("BAA", "BCC")),
                           ("period_trace_cost", ("BBA", "BBC"))]:
            a, b = pair
            y = poa.observe(self.rows[a], mode)
            self.assertEqual(y, poa.observe(self.rows[b], mode), "P_SAME_VIEW")
            audit = self.result["observations"][mode]
            self.assertFalse(audit["factors_through"], "P_NO_FACTORISATION")
            fibre = next(f for f in audit["fibres"] if a in f["histories"])
            self.assertIn(b, fibre["histories"], "P_FIBRE_POPULATION")
            self.assertEqual(fibre["decision"], "insufficient observation", "P_MIXED_FIBRE")
        rich = self.result["observations"]["period_cost_membership"]
        self.assertTrue(rich["factors_through"], "P_RICH_FACTORISATION")
        for fibre in rich["fibres"]:
            self.assertIn(fibre["decision"], ("admit", "reject"), "P_RICH_DECISIONS")

    def test_fibre_records(self):
        for mode, audit in self.result["observations"].items():
            fibres = audit["fibres"]
            listed = [word for fibre in fibres for word in fibre["histories"]]
            self.assertEqual(sorted(listed), sorted(self.rows), "P_FIBRE_PARTITION")
            values = [fibre["observation"] for fibre in fibres]
            self.assertEqual(len(values), len(set(values)), "P_FIBRE_UNIQUE")
            for fibre in fibres:
                self.assertTrue(fibre["histories"], "P_FIBRE_ATTAINED")
                for word in fibre["histories"]:
                    self.assertEqual(poa.observe(self.rows[word], mode),
                                     fibre["observation"], "P_FIBRE_OBSERVATION")
                # A and B fix eta; C does not, independently of adapter target wiring.
                labels = {"C" not in word for word in fibre["histories"]}
                expected = ("admit" if labels == {True} else
                            "reject" if labels == {False} else "insufficient observation")
                self.assertEqual(fibre["decision"], expected, "P_FIBRE_DECISION")

    def test_exact_projection(self):
        row = copy.deepcopy(self.rows["BAA"])
        expected_endpoint = (((0, 1),), ("1/3", "2/3", "1", "4/3"))
        expected_periods = (("1", "1", "1", "1"), expected_endpoint[1])
        self.assertEqual(poa.observe(row, "final_cycle_cost"), expected_endpoint, "P_ENDPOINT_PROJECTION")
        self.assertEqual(poa.observe(row, "period_trace_cost"), expected_periods, "P_PERIOD_PROJECTION")
        row["events"] = ["C", "C", "C"]
        row["P_eta_membership"] = [False, False, False]
        self.assertEqual(poa.observe(row, "final_cycle_cost"), expected_endpoint, "P_HIDDEN_ENDPOINT")
        self.assertEqual(poa.observe(row, "period_trace_cost"), expected_periods, "P_HIDDEN_PERIODS")
        self.assertNotEqual(poa.observe(row, "period_cost_membership"),
                            poa.observe(self.rows["BAA"], "period_cost_membership"), "P_RICH_EXPOSES_MEMBERSHIP")
        with self.assertRaisesRegex(ValueError, "^POA_UNKNOWN_OBSERVATION"):
            poa.observe(row, "not-a-view")

    def test_three_valued_decisions(self):
        # Literal target labels independent of membership computation.
        obs = lambda _: 0
        labels = {"good": True, "bad": False}
        api = self.data.poa
        for catalogue, expected in [(("good",), "admit"), (("bad",), "reject"),
                                    (("good", "bad"), "insufficient observation"),
                                    (("bad", "good"), "insufficient observation")]:
            self.assertEqual(api.fibre_decision(catalogue, obs, labels.__getitem__, 0).value,
                             expected, "P_DECISION")
        with self.assertRaisesRegex(ValueError, 'requested observation is not attained'):
            api.fibre_decision(("good", "bad"), obs, labels.__getitem__, 1)
        with self.assertRaisesRegex(identity.Refusal, "^POA_EMPTY_CATALOGUE$"):
            poa.audit_observation(api, {}, "final_cycle_cost")

    def test_provenance(self):
        self.assertEqual(set(self.result["commits"]), {"XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"}, "P_PINS")
        self.assertIn("poa_audit", self.result["source_provenance"], "P_SOURCE")
        record = self.result["source_provenance"]["poa_audit"]
        path = Path(record["path"])
        self.assertEqual(record["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), "P_SOURCE_SHA")
        self.assertEqual(path, Path(poa.__file__).resolve().parent / "layers/PoA/harness/seam_audit.py")

    def test_import_after_pin_check(self):
        with tempfile.TemporaryDirectory(prefix="tectonica-poa-import-") as directory:
            root = Path(directory)
            path = root / "layers/PoA/harness/seam_audit.py"
            path.parent.mkdir(parents=True)
            executed = root / "import-executed"
            path.write_text("from pathlib import Path\n"
                            + "Path(" + repr(str(executed)) + ").touch()\n"
                            + "raise AssertionError('P_IMPORT_BEFORE_PINS')\n", encoding="utf-8")
            with patch.dict(sys.modules):
                sys.modules.pop("tectonica_poa_audit", None)
                with patch.object(identity, "load_sources", side_effect=identity.Refusal("PIN_TEST")):
                    with self.assertRaisesRegex(identity.Refusal, "^PIN_TEST$"):
                        poa.load_sources(root)
            self.assertFalse(executed.exists(), "P_IMPORT_BEFORE_PINS")

    def test_import_after_pin_success(self):
        with tempfile.TemporaryDirectory(prefix="tectonica-poa-import-") as directory:
            root = Path(directory)
            layer = root / "layers/PoA"
            path = layer / "harness/seam_audit.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"EXPORTED_LITERAL = 17\n")
            fixture_git(layer, "init", "-q")
            fixture_git(layer, "add", "--", "harness/seam_audit.py")
            fixture_git(layer, "commit", "-qm", "benign PoA fixture")
            selected = {"PoA": (layer, fixture_git(layer, "rev-parse", "HEAD"))}
            stitch = SimpleNamespace(_load=lambda name, source:
                                     pinned_sources._load(selected, name, source))
            allowed = SimpleNamespace(stitch=stitch, provenance={})
            with patch.dict(sys.modules), patch.dict(pinned_sources._LOADED):
                sys.modules.pop("tectonica_poa_audit", None)
                pinned_sources._LOADED.pop("tectonica_poa_audit", None)
                with patch.object(identity, "load_sources", return_value=allowed):
                    result = poa.load_sources(root)
                self.assertEqual(result.poa.EXPORTED_LITERAL, 17, "P_IMPORT_AFTER_VALIDATION")
                self.assertEqual(Path(result.poa.__file__).resolve(), path.resolve(), "P_TEMP_SOURCE_EXECUTED")



if __name__ == "__main__":
    unittest.main()

