"""Mocked launch-contract tests and one real local Git fsmonitor regression."""
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import tectonica as app


class GitFsmonitorTests(unittest.TestCase):
    def test_tracked_fsmonitor_dirty(self):
        """A silent fsmonitor hook must not hide a changed tracked README."""
        with tempfile.TemporaryDirectory(prefix="tectonica-fsmonitor-") as temporary:
            root = Path(temporary).resolve()
            environment = {key: value for key, value in os.environ.items()
                           if not key.upper().startswith("GIT_")}

            def setup_git(*args):
                result = subprocess.run(["git", "-c", "core.fsmonitor=false",
                                         "-C", str(root), *args],
                                        capture_output=True, env=environment)
                self.assertEqual(result.returncode, 0,
                                 "T_FSMONITOR_SETUP: " + result.stderr.decode("utf-8", errors="replace"))

            setup_git("init")
            setup_git("config", "core.hooksPath", ".git/hooks")
            setup_git("config", "commit.gpgsign", "false")
            readme = root / "README.md"
            readme.write_bytes(b"Original benign README.\n")
            setup_git("add", "--", "README.md")
            setup_git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                      "commit", "-m", "Local disposable regression fixture")
            hook = root / ".git/hooks/fsmonitor-watchman"
            hook.write_bytes(b"#!/bin/sh\nexit 0\n")
            hook.chmod(0o755)
            setup_git("config", "core.fsmonitor", ".git/hooks/fsmonitor-watchman")
            setup_git("config", "core.fsmonitorHookVersion", "1")
            status = ("status", "--porcelain=v1", "--untracked-files=all", "--ignored")
            warm = subprocess.run(["git", "-C", str(root), *status],
                                  capture_output=True, env=environment)
            self.assertEqual(warm.returncode, 0, "T_FSMONITOR_WARM")
            self.assertEqual(warm.stderr, b"", "T_FSMONITOR_WARM_STDERR")
            self.assertEqual(warm.stdout, b"", "T_FSMONITOR_CLEAN_WARM")
            self.assertEqual(app.git_bytes(root, *status), b"", "T_FSMONITOR_CLEAN")
            readme.write_bytes(b"Changed benign README with a different length.\n")
            self.assertEqual(app.git_bytes(root, *status), b" M README.md\n", "T_FSMONITOR_DIRTY")


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tectonica-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.root_commit = "3" * 40
        self.responses = {(self.root, ("rev-parse", "--show-toplevel")): str(self.root),
                          (self.root, ("rev-parse", "HEAD")): self.root_commit}
        for name, revision in [("XIV", "a" * 40), ("XV", "b" * 40), ("Identity", "d" * 40), ("PoA", "e" * 40), ("Person", "f" * 40), ("ProbeVI", "1" * 40), ("DoubleFibre", "2" * 40)]:
            directory = self.root / "layers" / name
            directory.mkdir(parents=True)
            kind = "040000 tree " if name == "ProbeVI" else "160000 commit "
            self.responses[(self.root, ("ls-tree", "HEAD", "--", "layers/" + name))] = (
                kind + revision + "\tlayers/" + name)
            repository = self.root if name == "ProbeVI" else directory
            scope = ("--", "layers/ProbeVI") if name == "ProbeVI" else ()
            self.responses[(directory, ("rev-parse", "--show-toplevel"))] = str(repository)
            self.responses[(directory, ("rev-parse", "HEAD"))] = self.root_commit if name == "ProbeVI" else revision
            self.responses[(repository, ("ls-files", "-v", "-z") + scope)] = "H README.md\0"
            self.responses[(repository, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored") + scope)] = ""
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
        (self.root / "layers/Person/person_harness.py").write_text("# presence fixture\n", encoding="utf-8")
        probe_harness = self.root / "layers/ProbeVI/harness"
        probe_harness.mkdir()
        (probe_harness / "probe_vi.py").write_text("# presence fixture\n", encoding="utf-8")
        df_harness = self.root / "layers/DoubleFibre/harness"
        df_harness.mkdir()
        (df_harness / "double_fibre_audit.py").write_text("# presence fixture\n", encoding="utf-8")
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
        self.assertEqual(set(selected), {"XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"}, "T_ALL_LAYERS: seven bindings required")
        self.assertEqual(selected["ProbeVI"], (self.root / "layers/ProbeVI", self.root_commit),
                         "T_PROBE_ROOT_COMMIT: source uses root commit, not tree object")

    def test_project_root(self):
        self.responses[(self.root, ("rev-parse", "--show-toplevel"))] = str(self.root.parent)
        self.refusal("PROJECT_ROOT_REQUIRED", "T_PROJECT")

    def test_pin_records(self):
        for name in ["XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"]:
            key = (self.root, ("ls-tree", "HEAD", "--", "layers/" + name))
            original = self.responses[key]
            kind = "040000 tree" if name == "ProbeVI" else "160000 commit"
            other_kind = "160000 commit" if name == "ProbeVI" else "040000 tree"
            for bad in ["", original.replace(kind, "100644 blob"),
                        original.replace(kind, other_kind),
                        original.replace("layers/" + name, "layers/Other")]:
                self.responses[key] = bad
                self.refusal("PIN_REQUIRED: " + name, "T_PIN_RECORD")
            self.responses[key] = original

    def test_01_revision(self):
        for name in ["XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"]:
            key = (self.root / "layers" / name, ("rev-parse", "HEAD"))
            original = self.responses[key]
            self.responses[key] = "c" * 40
            self.refusal("REVISION_MISMATCH: " + name, "T_REVISION")
            self.responses[key] = original

    def test_dependency_root(self):
        for name in ["XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"]:
            key = (self.root / "layers" / name, ("rev-parse", "--show-toplevel"))
            original = self.responses[key]
            self.responses[key] = str(self.root / "layers/ProbeVI") if name == "ProbeVI" else str(self.root)
            self.refusal("DEPENDENCY_ROOT: " + name, "T_DEP_ROOT")
            self.responses[key] = original

    def test_dirty(self):
        for name in ["XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"]:
            repository = self.root if name == "ProbeVI" else self.root / "layers" / name
            scope = ("--", "layers/ProbeVI") if name == "ProbeVI" else ()
            key = (repository, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored") + scope)
            for dirty in [" M README.md", "?? extra.py", "!! ignored.py"]:
                self.responses[key] = dirty
                self.refusal("DEPENDENCY_DIRTY: " + name, "T_DIRTY")
            self.responses[key] = ""

    def test_hidden_flags(self):
        for name in ["XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"]:
            repository = self.root if name == "ProbeVI" else self.root / "layers" / name
            scope = ("--", "layers/ProbeVI") if name == "ProbeVI" else ()
            key = (repository, ("ls-files", "-v", "-z") + scope)
            for flag in ["h", "S", "s"]:
                self.responses[key] = flag + " README.md\0"
                self.refusal("HIDDEN_INDEX_FLAGS: " + name, "T_FLAGS")
            self.responses[key] = "H README.md\0"

    def test_probe_scope(self):
        self.responses[(self.root, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored"))] = " M README.md"
        self.responses[(self.root, ("ls-files", "-v", "-z"))] = "S README.md\0"
        selected = app.checked_layers(self.root)
        self.assertEqual(selected["ProbeVI"][1], self.root_commit, "T_PROBE_SCOPE_CONTROL")
        key = (self.root, ("status", "--porcelain=v1", "--untracked-files=all", "--ignored", "--", "layers/ProbeVI"))
        self.responses[key] = "!! layers/ProbeVI/harness/ignored.py"
        self.refusal("DEPENDENCY_DIRTY: ProbeVI", "T_PROBE_IGNORED")

    def test_probe_commit_required(self):
        self.responses[(self.root, ("rev-parse", "HEAD"))] = "HEAD"
        self.refusal("PIN_REQUIRED: ProbeVI", "T_PROBE_COMMIT")

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

    def test_person_source(self):
        path = self.root / "layers/Person/person_harness.py"
        self.assertTrue(path.is_file(), "T_PERSON_EXISTENCE_CONTROL")
        path.unlink()
        self.refusal("SOURCE_MISSING: Person/person_harness.py", "T_PERSON_SOURCE")

    def test_probe_source(self):
        path = self.root / "layers/ProbeVI/harness/probe_vi.py"
        self.assertTrue(path.is_file(), "T_PROBE_EXISTENCE_CONTROL")
        path.unlink()
        self.refusal("SOURCE_MISSING: ProbeVI/harness/probe_vi.py", "T_PROBE_SOURCE")

    def test_double_fibre_source(self):
        path = self.root / "layers/DoubleFibre/harness/double_fibre_audit.py"
        self.assertTrue(path.is_file(), "T_DF_EXISTENCE_CONTROL")
        path.unlink()
        self.refusal("SOURCE_MISSING: DoubleFibre/harness/double_fibre_audit.py", "T_DF_SOURCE")

    def test_double_fibre_launch(self):
        with patch.object(app, "ROOT", self.root), patch.object(app.subprocess, "run") as run:
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 7 + [subprocess.CompletedProcess([], 23)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 23, "T_DF_CHILD_STATUS")
            self.assertEqual(run.call_count, 8, "T_DF_RUN")
            child = run.call_args_list[7]
            self.assertEqual(child.args[0][-1], str(self.root / "double_fibre_stitch.py"), "T_DF_COMMAND")
            self.assertEqual(child.args[0][0], app.sys.executable, "T_DF_PYTHON")
            self.assertIn("-B", child.args[0], "T_DF_BYTECODE")
            expected = [] if not app.sys.flags.optimize else ["-" + "O" * app.sys.flags.optimize]
            self.assertEqual([a for a in child.args[0] if a in ("-O", "-OO")], expected, "T_DF_OPTIMIZATION")
            self.assertEqual(child.kwargs["cwd"], self.root, "T_DF_CWD")
            self.assertEqual(child.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_DF_ENV")

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
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 8
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 0, "T_ALL_CHILDREN_PASS")
            self.assertEqual(run.call_count, 8, "T_ALL_CHILDREN_RUN")
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
            run.reset_mock()
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 5 + [subprocess.CompletedProcess([], 17)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 17, "T_PERSON_CHILD_STATUS")
            self.assertEqual(run.call_count, 6, "T_PERSON_RUN")
            sixth = run.call_args_list[5]
            self.assertEqual(sixth.args[0][-1], str(self.root / "person_stitch.py"), "T_PERSON_COMMAND")
            self.assertEqual(sixth.args[0][0], app.sys.executable, "T_PERSON_PYTHON")
            self.assertIn("-B", sixth.args[0], "T_PERSON_BYTECODE")
            self.assertEqual([arg for arg in sixth.args[0] if arg in ("-O", "-OO")], expected, "T_PERSON_OPTIMIZATION")
            self.assertEqual(sixth.kwargs["cwd"], self.root, "T_PERSON_CWD")
            self.assertEqual(sixth.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_PERSON_BYTECODE_ENV")
            run.reset_mock()
            run.side_effect = [subprocess.CompletedProcess([], 0)] * 6 + [subprocess.CompletedProcess([], 19)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([]), 19, "T_COMMON_CONTROL_CHILD_STATUS")
            self.assertEqual(run.call_count, 7, "T_COMMON_CONTROL_RUN")
            seventh = run.call_args_list[6]
            self.assertEqual(seventh.args[0][-1], str(self.root / "common_control_stitch.py"), "T_COMMON_CONTROL_COMMAND")
            self.assertIn("-B", seventh.args[0], "T_COMMON_CONTROL_BYTECODE")
            self.assertEqual([arg for arg in seventh.args[0] if arg in ("-O", "-OO")], expected, "T_COMMON_CONTROL_OPTIMIZATION")
            self.assertEqual(seventh.kwargs["cwd"], self.root, "T_COMMON_CONTROL_CWD")
            self.assertEqual(seventh.kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1", "T_COMMON_CONTROL_BYTECODE_ENV")
            for name in ("XIV", "XV", "Identity", "PoA", "Person", "ProbeVI", "DoubleFibre"):
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

