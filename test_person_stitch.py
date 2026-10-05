"""Person loading and child refusal checks on the recorded dependencies."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

import pinned_sources
import person_stitch as app
import tectonica


class PersonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = tectonica.checked_layers(tectonica.ROOT)

    def test_pin_required(self):
        with self.assertRaisesRegex(tectonica.Refusal, "^PIN_REQUIRED: Person$"):
            app.load({})

    def test_verified_buffer_provenance(self):
        person = app.load(self.selected)
        directory, revision = self.selected["Person"]
        body = pinned_sources.read_pinned(self.selected, directory / "person_harness.py")
        self.assertEqual(person._xiv_stitch_source_sha256, hashlib.sha256(body).hexdigest())
        self.assertEqual(person.__file__, str((directory / "person_harness.py").resolve()))

    def test_tampered_buffer_refused(self):
        directory, _ = self.selected["Person"]
        source = (directory / "person_harness.py").resolve()
        read = Path.read_bytes
        def changed(path):
            body = read(path)
            return body + b"\n# content drift\n" if path.resolve() == source else body
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
                app.load(self.selected)

    def test_executes_single_verified_buffer(self):
        directory, _ = self.selected["Person"]
        source = (directory / "person_harness.py").resolve()
        read, calls = Path.read_bytes, []
        def once(path):
            if path.resolve() == source:
                calls.append(path)
                if len(calls) != 1:
                    raise RuntimeError("SECOND_BUFFER_READ")
            return read(path)
        with patch.dict(sys.modules), patch.dict(pinned_sources._LOADED, clear=True):
            sys.modules.pop("tectonica_person", None)
            with patch.object(Path, "read_bytes", once):
                person = app.load(self.selected)
            self.assertEqual(len(calls), 1, "PERSON_ONE_VERIFIED_READ")
            self.assertEqual(person.prefix_budgets((person.Window(app.F(1, 3), 2),), app.F(2)),
                             ((app.F(5, 3), 2),), "PERSON_VERIFIED_BUFFER_EXECUTED")

    def test_foreign_module_refused(self):
        with patch.dict(sys.modules, {"tectonica_person": ModuleType("tectonica_person")}), \
             patch.dict(pinned_sources._LOADED, clear=True):
            with self.assertRaisesRegex(tectonica.Refusal, "^PINNED_MODULE_CONFLICT: tectonica_person$"):
                app.load(self.selected)

    def test_child_refusal_status(self):
        with patch.object(app, "fixture", side_effect=tectonica.Refusal("PIN_REQUIRED: Person")), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as error:
            self.assertEqual(app.main([]), 2, "PERSON_REFUSED_STATUS")
            self.assertIn("PERSON_CONNECTION: REFUSED PIN_REQUIRED: Person", error.getvalue())

    def test_correct_scientific_reject_is_success(self):
        data = app.fixture(tectonica.ROOT)
        report = app.result(data)
        costly = report["cases"]["costly"]["complete_routes"][0]
        self.assertFalse(costly["final_survival"])
        self.assertFalse(costly["whole_survival"])
        self.assertEqual(costly["first_crossing"], (3, 3))
        self.assertEqual(report["cases"]["cut"]["complete_routes"], [])
        with patch.object(app, "fixture", return_value=data), redirect_stdout(io.StringIO()):
            self.assertEqual(app.main(["--teeth"]), 0, "PERSON_REJECT_IS_COMPUTED")
        with patch.object(app, "fixture", return_value=data), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(app.main([]), 0, "PERSON_REPORT_STATUS")
        rendered = output.getvalue()
        self.assertIn("PERSON_CONNECTION: PASS", rendered, "PERSON_REPORT_PASS")
        decoded = json.JSONDecoder().raw_decode(rendered[rendered.index("{"):])[0]
        negative = decoded["cases"]["costly"]["complete_routes"][0]
        self.assertEqual(negative["first_crossing"], [3, 3], "PERSON_REPORT_CROSSING")
        self.assertEqual(negative["prefix_budgets"],
                         [["5/3", 1], ["2/3", 2], ["-1/3", 3], ["-2/3", 4]],
                         "PERSON_REPORT_PREFIX_BUDGETS")
        self.assertFalse(negative["whole_survival"], "PERSON_REPORT_NEGATIVE_SURVIVAL")


if __name__ == "__main__":
    unittest.main()
