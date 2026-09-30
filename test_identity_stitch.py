"""Integration checks using actual pinned sources and isolated in-memory corruptions."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import identity_stitch as app


class ConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = app.load_sources(Path(__file__).resolve().parent)

    def run_word(self, word='BC', windows=None, capacity=F(2)):
        if windows is None:
            windows = [([j], {j: F(1, 3)}) for j in range(len(word) + 1)]
        return app.connect(self.data, word, windows, len(windows), 1, capacity)

    def refused(self, marker, operation):
        with self.assertRaises(app.Refusal) as caught:
            operation()
        self.assertEqual(str(caught.exception), marker, 'wrong first refusal')

    def test_literal_examples(self):
        expected = {
            'ABAB': (['1', '1', '1', '1', '1'], 'PRESERVING', '1/3'),
            'BC': (['1', '1', '0'], 'ANNIHILATING', '1'),
            'CB': (['1', '-1', '-1'], 'PRESERVING', '1'),
            'BCC': (['1', '1', '0', '1'], 'PRESERVING', '2/3'),
        }
        rows = app.examples(self.data)
        self.assertEqual([''.join(row['events']) for row in rows], ['ABAB', 'BC', 'CB', 'BCC'])
        for row in rows:
            word = ''.join(row['events'])
            periods, verdict, slack = expected[word]
            self.assertEqual(row['periods'], periods)
            self.assertEqual(row['pairing_verdict'], verdict)
            self.assertEqual(row['pairing_survived'], verdict == 'PRESERVING')
            self.assertIs(row['global_class_zero'], False)
            self.assertEqual(row['ie'], {'verdict': 'NESTED-BOUNDARY', 'steps': len(periods),
                'first_crossing': len(periods), 'upper_slack': slack, 'm_IE': '0',
                'scope': 'formal constructed IE witness; no autonomy or deployment evidence'})
            self.assertEqual(row['full_regime_w'], 'NOT_EVALUATED')
        self.assertTrue(rows[0]['period_constant'])
        self.assertFalse(rows[2]['period_constant'])
        self.assertFalse(rows[3]['period_constant'])
        self.assertEqual(rows[1]['cycles'], [{0: 1, 1: -1}, {0: 1}, {1: 1}])
        self.assertEqual(rows[3]['cycles'][-1], {0: 1})
        self.assertEqual(rows[1]['cumulative_costs'], ['1/3', '2/3', '1'])
        self.assertEqual(rows[1]['cumulative_costs'], rows[2]['cumulative_costs'])

    def test_each_window_is_accounted(self):
        windows = [([0], {0: F(1, 10)}), ([1], {1: F(1, 5)}), ([2], {2: F(1, 4)})]
        row = self.run_word(windows=windows)
        self.assertEqual(row['cumulative_costs'], ['1/10', '3/10', '11/20'])
        self.assertEqual(row['accounting_prefix_burdens'], ['1/10', '3/10', '11/20'])
        self.assertEqual(row['ie']['upper_slack'], '29/20')
        # Two concurrent channels still produce one accounting edge per window.
        row = app.connect(self.data, 'BC', [([0, 1], {0: F(1, 10), 1: F(1, 5)}),
            ([2], {2: F(1, 4)}), ([], {})], 3, 2, F(2))
        self.assertEqual(row['cumulative_costs'], ['3/10', '11/20', '11/20'])
        self.assertEqual(row['ie']['steps'], 3)


    def test_omitted_increments_are_zero(self):
        row = self.run_word(windows=[([j], {}) for j in range(3)])
        self.assertEqual(row['cumulative_costs'], ['0', '0', '0'])
        self.assertEqual(row['accounting_prefix_burdens'], ['0', '0', '0'])
        self.assertEqual(row['ie']['verdict'], 'NESTED-BOUNDARY')

    def test_active_iterators_are_consumed_once(self):
        row = self.run_word(windows=[(iter([j]), {j: F(1, 3)}) for j in range(3)])
        self.assertEqual(row['accounting_prefix_burdens'], ['1/3', '2/3', '1'])
        self.assertEqual(row['ie']['verdict'], 'NESTED-BOUNDARY')

    def test_certificate_tampering(self):
        bad = deepcopy(self.data.certificate)
        bad['order_effect']['initial_cycle'][0] += 1
        with self.assertRaisesRegex(app.Refusal, '^CERTIFICATE_REJECTED:'):
            app.verify_certificate(self.data.replay, bad)
        app.verify_certificate(self.data.replay, self.data.certificate)

    def test_import_after_pin_check(self):
        with tempfile.TemporaryDirectory(prefix="tectonica-identity-import-") as directory:
            root = Path(directory)
            path = root / "layers/XV/harness/xiv_stitch.py"
            path.parent.mkdir(parents=True)
            executed = root / "import-executed"
            path.write_text("from pathlib import Path\n"
                            + "Path(" + repr(str(executed)) + ").touch()\n"
                            + "raise AssertionError('I_IMPORT_BEFORE_PINS')\n", encoding="utf-8")
            with patch.object(app.tectonica, "checked_layers", side_effect=app.tectonica.Refusal("PIN_TEST")):
                with self.assertRaisesRegex(app.tectonica.Refusal, "^PIN_TEST$"):
                    app.load_sources(root)
            self.assertFalse(executed.exists(), "I_IMPORT_BEFORE_PINS")

    def test_provenance_binds_loaded_files(self):
        for name in ('xiv_stitch', 'identity_transport', 'identity_replay', 'identity_certificate'):
            record = self.data.provenance[name]
            self.assertEqual(record['sha256'], hashlib.sha256(Path(record['path']).read_bytes()).hexdigest())
        self.assertEqual(set(self.data.commits), {'XIV', 'XV', 'Identity', 'PoA'})

    def test_wrong_cycle_in_period_kernel(self):
        original = self.data.api.graph.induced_pushforward
        def wrong_cycle(emap, z):
            result = dict(original(emap, z))
            result[1] = result.get(1, 0) + 1  # eta has zero on this coordinate.
            return result
        with patch.object(self.data.api.graph, 'induced_pushforward', side_effect=wrong_cycle):
            self.refused('CYCLE_TRANSPORT_AGREEMENT', self.run_word)

    def test_wrong_composition(self):
        with patch.object(app, 'compose', side_effect=lambda first, second: deepcopy(first)):
            self.refused('COMPOSED_TRANSPORT_AGREEMENT', self.run_word)

    def test_signed_path_composition(self):
        first = {0: [(1, -1)], 1: [(0, 1)]}
        second = {0: [(0, 1)], 1: [(0, 1), (1, -1)]}
        self.assertEqual(app.compose(first, second), {0: [(1, 1), (0, -1)], 1: [(0, 1)]})
        identity = {0: [(0, 1)], 1: [(1, 1)]}
        self.assertEqual(app.compose(first, identity), first)
        self.assertEqual(app.compose(identity, second), second)

    def test_wrong_period_trace(self):
        original = self.data.identity.Schedule.run
        def wrong_period(schedule, *args, **kwargs):
            periods, budgets = original(schedule, *args, **kwargs)
            return periods[:-1] + [periods[-1] + 1], budgets
        with patch.object(self.data.identity.Schedule, 'run', new=wrong_period):
            self.refused('PERIOD_TRACE_AGREEMENT', self.run_word)

    def test_wrong_survival_projection(self):
        original = self.data.api.core.transport_classify
        def wrong_survival(*args):
            verdict, survived = original(*args)
            return verdict, [not value for value in survived]
        with patch.object(self.data.api.core, 'transport_classify', side_effect=wrong_survival):
            self.refused('PAIRING_SURVIVAL_AGREEMENT', self.run_word)

    def test_wrong_verdict_label(self):
        original = self.data.api.core.transport_classify
        def wrong_verdict(*args):
            verdict, survived = original(*args)
            return 'PRESERVING' if verdict == 'ANNIHILATING' else 'ANNIHILATING', survived
        with patch.object(self.data.api.core, 'transport_classify', side_effect=wrong_verdict):
            self.refused('TRANSPORT_VERDICT_AGREEMENT', self.run_word)

    def test_prefix_mismatch_with_same_final_cost(self):
        original = app.accounting_substrate
        def shifted_cost(data, windows, capacity):
            other = deepcopy(windows)
            other[0][1][0] += F(1, 10)
            other[1][1][1] -= F(1, 10)
            return original(data, other, capacity)
        with patch.object(app, 'accounting_substrate', side_effect=shifted_cost):
            self.refused('WINDOW_ACCOUNTING_AGREEMENT', self.run_word)

    def test_cancelling_path_control(self):
        original = app.certified_model
        def backtracks(data):
            maps, eta, gamma = original(data)
            return {name: {e: path + [(0, 1), (0, -1)] for e, path in emap.items()}
                    for name, emap in maps.items()}, eta, gamma
        baseline = self.run_word('CB')
        with patch.object(app, 'certified_model', side_effect=backtracks):
            self.assertEqual(self.run_word('CB'), baseline)

    def test_wrong_global_class_diagnostic(self):
        with patch.object(self.data.stitch, 'global_class_zero', return_value=True):
            self.refused('EXAMPLE_NONZERO_GLOBAL_CLASS_ABAB', lambda: app.examples(self.data))

    def test_explicit_input_domain(self):
        self.refused('WINDOW_SWITCH_COUNT', lambda: app.connect(self.data, 'BC', [], 3, 1, F(2)))
        self.refused('UNKNOWN_EVENT', lambda: self.run_word('BX'))
        for capacity in (0, -1, 2.0, True, None):
            self.refused('FINITE_POSITIVE_EXACT_CAPACITY', lambda: self.run_word(capacity=capacity))
        with self.assertRaisesRegex(self.data.stitch.Refusal, '^UPPER_SUBCRITICAL_REQUIRED$'):
            self.run_word(capacity=F(1))


if __name__ == '__main__':
    unittest.main()
