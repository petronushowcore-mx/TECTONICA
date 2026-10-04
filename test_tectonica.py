"""Local launch-contract tests with explicit Git-response fixtures; no repository is created."""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import tectonica as app


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tectonica-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.responses = {(self.root, ("rev-parse", "--show-toplevel")): str(self.root)}
        for name, revision in [("XIV", "a" * 40), ("XV", "b" * 40), ("Identity", "d" * 40), ("PoA", "e" * 40)]:
            directory = self.root / "layers" / name
            directory.mkdir(parents=True)
            self.responses[(self.root, ("ls-tree", "HEAD", "--", "layers/" + name))] = (
                "160000 commit " + revision + "\tlayers/" + name)
            self.responses[(directory, ("rev-parse", "--show-toplevel"))] = str(directory)
            self.responses[(directory, ("rev-parse", "HEAD"))] = revision
            self.responses[(directory, ("ls-files", "-v", "-z"))] = "H README.md\0"
            self.responses[(directory, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored"))] = ""
        self.runner = self.root / "layers/XV/harness/xiv_stitch.py"
        self.runner.parent.mkdir()
        self.runner.write_text("# launch fixture\n", encoding="utf-8")
        identity_harness = self.root / "layers/Identity/harness"
        identity_harness.mkdir()
        for source in ("switch_transport.py", "emergence_verify.py", "emergence_certificate.json"):
            (identity_harness / source).write_text("# presence fixture\n", encoding="utf-8")
        poa_harness = self.root / "layers/PoA/harness"
        poa_harness.mkdir()
        (poa_harness / "seam_audit.py").write_text("# presence fixture\n", encoding="utf-8")
        self.fixture = patch.object(app, "git", side_effect=lambda root, *args: self.responses[(Path(root), args)])
        self.fixture.start()
        self.addCleanup(self.fixture.stop)

    def refusal(self, reason, marker):
        try:
            app.checked_layers(self.root)
        except app.Refusal as exc:
            self.assertEqual(str(exc), reason, marker + ": wrong first refusal")
        except Exception as exc:
            self.fail(marker + ": unexpected " + type(exc).__name__)
        else:
            self.fail(marker + ": invalid dependency accepted")

    def test_00_honest(self):
        try:
            selected = app.checked_layers(self.root)
        except app.Refusal as exc:
            self.fail("T_HONEST: " + str(exc))
        self.assertEqual(set(selected), {"XIV", "XV", "Identity", "PoA"}, "T_ALL_LAYERS: four dependencies required")

    def test_project_root(self):
        self.responses[(self.root, ("rev-parse", "--show-toplevel"))] = str(self.root.parent)
        self.refusal("PROJECT_ROOT_REQUIRED", "T_PROJECT")

    def test_pin_records(self):
        for name in ["XIV", "XV", "Identity", "PoA"]:
            key = (self.root, ("ls-tree", "HEAD", "--", "layers/" + name))
            original = self.responses[key]
            for bad in ["", original.replace("160000 commit", "100644 blob"),
                        original.replace("layers/" + name, "layers/Other")]:
                self.responses[key] = bad
                self.refusal("PIN_REQUIRED: " + name, "T_PIN_RECORD")
            self.responses[key] = original

    def test_01_revision(self):
        for name in ["XIV", "XV", "Identity", "PoA"]:
            key = (self.root / "layers" / name, ("rev-parse", "HEAD"))
            original = self.responses[key]
            self.responses[key] = "c" * 40
            self.refusal("REVISION_MISMATCH: " + name, "T_REVISION")
            self.responses[key] = original

    def test_dependency_root(self):
        for name in ["XIV", "XV", "Identity", "PoA"]:
            key = (self.root / "layers" / name, ("rev-parse", "--show-toplevel"))
            original = self.responses[key]
            self.responses[key] = str(self.root)
            self.refusal("DEPENDENCY_ROOT: " + name, "T_DEP_ROOT")
            self.responses[key] = original

    def test_dirty(self):
        for name in ["XIV", "XV", "Identity", "PoA"]:
            key = (self.root / "layers" / name, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored"))
            for dirty in [" M README.md", "?? extra.py", "!! ignored.py"]:
                self.responses[key] = dirty
                self.refusal("DEPENDENCY_DIRTY: " + name, "T_DIRTY")
            self.responses[key] = ""

    def test_hidden_flags(self):
        for name in ["XIV", "XV", "Identity", "PoA"]:
            key = (self.root / "layers" / name, ("ls-files", "-v", "-z"))
            for flag in ["h", "S", "s"]:
                self.responses[key] = flag + " README.md\0"
                self.refusal("HIDDEN_INDEX_FLAGS: " + name, "T_FLAGS")
            self.responses[key] = "H README.md\0"

    def test_missing(self):
        with patch.object(Path, "is_dir", return_value=False):
            self.refusal("DEPENDENCY_MISSING: XIV", "T_MISSING")
        with patch.object(Path, "is_file", return_value=False):
            self.refusal("RUNNER_MISSING: XV", "T_RUNNER")

    def test_identity_sources(self):
        for source in ("switch_transport.py", "emergence_verify.py", "emergence_certificate.json"):
            path = self.root / "layers/Identity/harness" / source
            body = path.read_bytes()
            path.unlink()
            self.refusal("SOURCE_MISSING: Identity/" + source, "T_IDENTITY_SOURCE")
            path.write_bytes(body)

    def test_poa_source(self):
        path = self.root / "layers/PoA/harness/seam_audit.py"
        path.unlink()
        self.refusal("SOURCE_MISSING: PoA/seam_audit.py", "T_POA_SOURCE")

    def test_launch(self):
        with patch.object(app, "ROOT", self.root), patch.object(app.subprocess, "run") as run:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main(["--check-only"]), 0, "T_CHECK_ONLY")
                run.assert_not_called()
                run.side_effect = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 5)]
                self.assertEqual(app.main([]), 5, "T_IDENTITY_CHILD_STATUS")
            first, second = run.call_args_list
            self.assertEqual(first.args[0][-1], str(self.root / "pinned_sources.py"),
                             "T_XIV_COMMAND")
            self.assertEqual(second.args[0][-1], str(self.root / "identity_stitch.py"), "T_IDENTITY_COMMAND")
            for call in (first, second):
                command = call.args[0]
                self.assertIn("-B", command, "T_BYTECODE")
                expected = [] if not app.sys.flags.optimize else ["-" + "O" * app.sys.flags.optimize]
                self.assertEqual([arg for arg in command if arg in ("-O", "-OO")], expected, "T_OPTIMIZATION")
                self.assertEqual(call.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_BYTECODE_ENV")
            run.reset_mock(side_effect=True)
            run.return_value = subprocess.CompletedProcess([], 7)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 7, "T_XIV_CHILD_STATUS")
            self.assertEqual(run.call_count, 1, "T_STOP_AFTER_FAILED_XIV")
            run.reset_mock()
            run.side_effect = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0),
                               subprocess.CompletedProcess([], 9)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 9, "T_POA_CHILD_STATUS")
            self.assertEqual(run.call_count, 3, "T_POA_RUN")
            third = run.call_args_list[2]
            self.assertEqual(third.args[0][-1], str(self.root / "poa_stitch.py"), "T_POA_COMMAND")
            self.assertIn("-B", third.args[0], "T_POA_BYTECODE")
            self.assertEqual([arg for arg in third.args[0] if arg in ("-O", "-OO")], expected, "T_POA_OPTIMIZATION")
            self.assertEqual(third.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_POA_BYTECODE_ENV")
            run.reset_mock()
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 3 + [subprocess.CompletedProcess([], 11)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 11, "T_RECOMPOSITION_CHILD_STATUS")
            self.assertEqual(run.call_count, 4, "T_RECOMPOSITION_RUN")
            fourth = run.call_args_list[3]
            self.assertEqual(fourth.args[0][-1], str(self.root / "recomposition_stitch.py"), "T_RECOMPOSITION_COMMAND")
            self.assertIn("-B", fourth.args[0], "T_RECOMPOSITION_BYTECODE")
            self.assertEqual([arg for arg in fourth.args[0] if arg in ("-O", "-OO")], expected, "T_RECOMPOSITION_OPTIMIZATION")
            self.assertEqual(fourth.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_RECOMPOSITION_BYTECODE_ENV")
            run.reset_mock()
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 5
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 0, "T_ALL_CHILDREN_PASS")
            self.assertEqual(run.call_count, 5, "T_ALL_CHILDREN_RUN")
            fifth = run.call_args_list[4]
            self.assertEqual(fifth.args[0][-2:],
                             [str(self.root / "severance_stitch.py"), "--teeth"], "T_SEVERANCE_COMMAND")
            self.assertEqual(fifth.args[0][0], app.sys.executable, "T_SEVERANCE_PYTHON")
            self.assertIn("-B", fifth.args[0], "T_SEVERANCE_BYTECODE")
            self.assertEqual([arg for arg in fifth.args[0] if arg in ("-O", "-OO")],
                             expected, "T_SEVERANCE_OPTIMIZATION")
            self.assertEqual(fifth.kwargs["cwd"], self.root, "T_SEVERANCE_CWD")
            self.assertEqual(fifth.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1",
                             "T_SEVERANCE_BYTECODE_ENV")
            run.reset_mock()
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 4 + [subprocess.CompletedProcess([], 13), subprocess.CompletedProcess([], 0)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 13, "T_SEVERANCE_CHILD_STATUS")
            self.assertEqual(run.call_count, 5, "T_STOP_AFTER_FAILED_SEVERANCE")
            for name in ("XIV", "XV", "Identity", "PoA"):
                run.reset_mock()
                key = (self.root / "layers" / name, ("rev-parse", "HEAD"))
                original = self.responses[key]
                self.responses[key] = "c" * 40
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(app.main([]), 2, "T_NO_LAUNCH_" + name)
                run.assert_not_called()
                self.responses[key] = original


if __name__ == "__main__":
    unittest.main()
