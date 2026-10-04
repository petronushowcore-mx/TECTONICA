"""Contracts of the finite boundary recomposition adapter on substituted carriers.

The pinned accounting carrier itself is read by the launcher's fourth child,
`recomposition_stitch.py`, not by these tests.
"""
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction as F
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import identity_stitch
import poa_stitch
import recomposition_stitch as app
import tectonica


class RecompositionTests(unittest.TestCase):
    def setUp(self):
        self.upper = SimpleNamespace(X=set(range(5)), E=set(zip(range(4), range(1, 5))),
                                     C=F(2), phi_edge=lambda pair: F(1, 3))
        self.base = SimpleNamespace(poa=object(), commits={"PoA": "fixture"}, provenance={"fixture": True})

    def fixture(self):
        with patch.object(poa_stitch, "load_sources", return_value=self.base) as load, \
             patch.object(identity_stitch, "accounting_substrate", return_value=(self.upper, tuple(range(5)))):
            data = app.fixture(Path("source-fixture"))
            load.assert_called_once_with(Path("source-fixture"))
            return data

    def test_fixture(self):
        data = self.fixture()
        self.assertIs(data["base"], self.base)
        self.assertEqual(app.routes(data["graph"]), (((0, 1, 2, 3, 4), F(4, 3), 4),))
        self.assertEqual(data["source_provenance"], self.base.provenance)

    def test_source_edges(self):
        self.upper.E.add((0, 4))
        with self.assertRaisesRegex(app.Refusal, "^SOURCE_EDGE_SET$"):
            self.fixture()

    def test_source_vertices(self):
        self.upper.X.add(5)
        with self.assertRaisesRegex(app.Refusal, "^SOURCE_VERTEX_SET$"):
            self.fixture()

    def test_source_capacity(self):
        self.upper.C = F(3)
        data = self.fixture()
        self.assertEqual(data["graph"].capacity, F(3), "SOURCE_CAPACITY_FIDELITY")

    def test_source_costs(self):
        self.upper.phi_edge = lambda pair: F(1, 4)
        with self.assertRaisesRegex(app.Refusal, "^ACTUAL_EDGE_COSTS$"):
            self.fixture()

    def test_checks_precede_success(self):
        with patch.object(app, "fixture", return_value={}), patch.object(app, "teeth", return_value=False), \
             patch.object(app, "result") as report, redirect_stdout(io.StringIO()):
            self.assertEqual(app.main([]), 1, "RECOMPOSITION_CHECK_FAILURE")
            report.assert_not_called()

    def test_source_refusal(self):
        with patch.object(app, "fixture", side_effect=tectonica.Refusal("SOURCE_CONTENT_MISMATCH")), \
             patch.object(app, "teeth") as checks, redirect_stderr(io.StringIO()) as error:
            self.assertEqual(app.main([]), 2)
            checks.assert_not_called()
            self.assertIn("SOURCE_CONTENT_MISMATCH", error.getvalue())


if __name__ == "__main__":
    unittest.main()
