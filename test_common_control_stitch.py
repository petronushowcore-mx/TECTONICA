"""Probe VI source binding and expected scientific rejection at the child boundary."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch
import tectonica
import pinned_sources
import common_control_stitch as app

class CommonControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = tectonica.checked_layers(tectonica.ROOT)

    def test_pin_required(self):
        with self.assertRaisesRegex(tectonica.Refusal, "^PIN_REQUIRED: ProbeVI$"):
            app.load({})

    def test_verified_buffer(self):
        source = Path(self.selected["ProbeVI"][0]) / "harness/probe_vi.py"
        module = app.load(self.selected)
        body = pinned_sources.read_pinned(self.selected, source)
        self.assertEqual(module.__file__, str(source.resolve()))
        self.assertEqual(module._xiv_stitch_source_sha256, hashlib.sha256(body).hexdigest())

    def test_tampered_buffer(self):
        source = (Path(self.selected["ProbeVI"][0]) / "harness/probe_vi.py").resolve()
        original = Path.read_bytes
        def tamper(path):
            body = original(path)
            return body + b"\n# drift\n" if path.resolve() == source else body
        with patch.object(Path, "read_bytes", tamper):
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
                app.load(self.selected)

    def test_foreign_module(self):
        with patch.dict(sys.modules, {"tectonica_probe_vi": ModuleType("tectonica_probe_vi")}), \
             patch.dict(pinned_sources._LOADED, clear=True):
            with self.assertRaisesRegex(tectonica.Refusal, "^PINNED_MODULE_CONFLICT:"):
                app.load(self.selected)

    def test_single_consumed_buffer(self):
        source = (Path(self.selected["ProbeVI"][0]) / "harness/probe_vi.py").resolve()
        original, calls = Path.read_bytes, []
        def once(path):
            body = original(path)
            if path.resolve() == source:
                calls.append(body)
                if len(calls) != 1:
                    raise RuntimeError("SECOND_BUFFER")
            return body
        with patch.dict(sys.modules), patch.dict(pinned_sources._LOADED, clear=True):
            sys.modules.pop("tectonica_probe_vi", None)
            with patch.object(Path, "read_bytes", once):
                module = app.load(self.selected)
            self.assertEqual(len(calls), 1)
            self.assertEqual(module._xiv_stitch_source_sha256, hashlib.sha256(calls[0]).hexdigest())
            self.assertEqual(module.check_sum_rate(module.ProbeModel())["d_dt_x1_plus_x2"], "2")

    def test_scientific_obstruction_is_success(self):
        with patch.object(tectonica, "checked_layers", return_value=self.selected), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(app.main(), 0)
        self.assertIn("PROVED_CANONICAL_OBSTRUCTION", output.getvalue())
        self.assertIn("COMMON_CONTROL_CONNECTION: PASS", output.getvalue())

    def test_typed_index_and_independent_target(self):
        probe, poa = app.load(self.selected), app.load_poa(self.selected)
        rows = app.catalogue(probe)
        with patch.object(poa, "factors_through", wraps=poa.factors_through) as factor:
            result = app.audit(poa, rows, "local_viability")
        histories, observation, predicate = factor.call_args.args
        self.assertEqual(len(histories), 3)
        self.assertTrue(all(poa.well_typed(history) and len(history) == 1 for history in histories))
        self.assertEqual(tuple(predicate(history) for history in histories), (False, True, True))
        self.assertTrue(all(history[0].admitted for history in histories))
        self.assertEqual(tuple(observation(history) for history in histories), ((True, True),)*3)
        self.assertFalse(result["factors_through"])

    def test_exact_output_domain(self):
        rendered = json.dumps({"exact": app.adapter.Q(1, 3)}, default=app.encode_exact)
        self.assertEqual(json.loads(rendered), {"exact": "1/3"}, "C_FRACTION_OUTPUT")
        with self.assertRaisesRegex(TypeError, "^COMMON_CONTROL_REPORT_TYPE: object$"):
            json.dumps({"unexpected": object()}, default=app.encode_exact)

    def test_refused_child(self):
        with patch.object(tectonica, "checked_layers", side_effect=tectonica.Refusal("PIN_REQUIRED: ProbeVI")), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as error:
            self.assertEqual(app.main(), 2)
        self.assertIn("COMMON_CONTROL_CONNECTION: REFUSED PIN_REQUIRED: ProbeVI", error.getvalue())

if __name__ == "__main__":
    unittest.main()


