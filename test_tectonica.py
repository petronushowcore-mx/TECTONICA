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
        for name, revision in [("XIV", "a" * 40), ("XV", "b" * 40)]:
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
        self.assertEqual(set(selected), {"XIV", "XV"}, "T_BOTH: two dependencies required")

    def test_project_root(self):
        self.responses[(self.root, ("rev-parse", "--show-toplevel"))] = str(self.root.parent)
        self.refusal("PROJECT_ROOT_REQUIRED", "T_PROJECT")

    def test_pin_records(self):
        for name in ["XIV", "XV"]:
            key = (self.root, ("ls-tree", "HEAD", "--", "layers/" + name))
            original = self.responses[key]
            for bad in ["", original.replace("160000 commit", "100644 blob"),
                        original.replace("layers/" + name, "layers/Other")]:
                self.responses[key] = bad
                self.refusal("PIN_REQUIRED: " + name, "T_PIN_RECORD")
            self.responses[key] = original

    def test_01_revision(self):
        for name in ["XIV", "XV"]:
            key = (self.root / "layers" / name, ("rev-parse", "HEAD"))
            original = self.responses[key]
            self.responses[key] = "c" * 40
            self.refusal("REVISION_MISMATCH: " + name, "T_REVISION")
            self.responses[key] = original

    def test_dependency_root(self):
        for name in ["XIV", "XV"]:
            key = (self.root / "layers" / name, ("rev-parse", "--show-toplevel"))
            original = self.responses[key]
            self.responses[key] = str(self.root)
            self.refusal("DEPENDENCY_ROOT: " + name, "T_DEP_ROOT")
            self.responses[key] = original

    def test_dirty(self):
        for name in ["XIV", "XV"]:
            key = (self.root / "layers" / name, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored"))
            for dirty in [" M README.md", "?? extra.py", "!! ignored.py"]:
                self.responses[key] = dirty
                self.refusal("DEPENDENCY_DIRTY: " + name, "T_DIRTY")
            self.responses[key] = ""

    def test_hidden_flags(self):
        for name in ["XIV", "XV"]:
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

    def test_launch(self):
        with patch.object(app, "ROOT", self.root), patch.object(app.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 5)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main(["--check-only"]), 0, "T_CHECK_ONLY")
                run.assert_not_called()
                self.assertEqual(app.main([]), 5, "T_CHILD_STATUS")
            command = run.call_args.args[0]
            self.assertEqual(command[-4:], [str(self.runner), "--xiv-root", str(self.root / "layers/XIV"), "--teeth"], "T_COMMAND")
            self.assertIn("-B", command, "T_BYTECODE")
            expected_optimization = [] if not app.sys.flags.optimize else ["-" + "O" * app.sys.flags.optimize]
            self.assertTrue([arg for arg in command if arg in ("-O", "-OO")] == expected_optimization, "T_OPTIMIZATION")
            self.assertEqual(run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_BYTECODE")
            # The earlier revision check verifies the refusal; here we also require no child launch.
            run.reset_mock()
            self.responses[(self.root / "layers/XIV", ("rev-parse", "HEAD"))] = "c" * 40
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 2, "T_NO_LAUNCH")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
