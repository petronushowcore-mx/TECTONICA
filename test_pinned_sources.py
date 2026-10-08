"""Bounded source-binding tests; fixtures are disposable local Git repositories."""
import hashlib
import os
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import tectonica
import pinned_sources as pinned
import identity_stitch as identity

LITERAL = b"VALUE = 17\n"
CHANGED = b"VALUE = 23\n"


def fixture_git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    empty_hooks = Path(root) / ".fixture-empty-hooks"
    empty_hooks.mkdir(exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "core.autocrlf=false",
         "-c", "core.hooksPath=" + str(empty_hooks),
         "-c", "commit.gpgsign=false", "-c", "user.name=Fixture",
         "-c", "user.email=fixture@example.invalid", *args],
        env=env, capture_output=True, stdin=subprocess.DEVNULL, timeout=15)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout.strip().decode("ascii")


class PinnedSourcesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pinned-fixture-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / "layer"
        self.repo.mkdir()
        self.path = self.repo / "literal.py"
        self.path.write_bytes(LITERAL)
        self.certificate = self.repo / "harness/emergence_certificate.json"
        self.certificate.parent.mkdir()
        self.certificate.write_bytes(b'{"value":17}\n')
        self.entry = self.repo / "harness/xiv_stitch.py"
        self.entry.write_bytes(LITERAL)
        fixture_git(self.repo, "init", "-q")
        fixture_git(self.repo, "add", "--", "literal.py", "harness")
        fixture_git(self.repo, "commit", "-qm", "benign fixture")
        self.commit = fixture_git(self.repo, "rev-parse", "HEAD")
        self.selected = {"XV": (self.repo, self.commit)}
        self.name = "_pinned_fixture_" + self.root.name.replace("-", "_")
        self.addCleanup(pinned._LOADED.pop, self.name, None)
        self.addCleanup(sys.modules.pop, self.name, None)

    def test_exact_and_crlf(self):
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL, "S_EXACT")
        self.path.write_bytes(b"VALUE = 17\r\n")
        self.assertEqual(pinned.read_pinned(self.selected, self.path), b"VALUE = 17\r\n", "S_CRLF")
        module = pinned._load(self.selected, self.name, self.path)
        self.assertEqual(module.VALUE, 17, "S_LITERAL")
        self.assertEqual(module._xiv_stitch_source_sha256,
                         hashlib.sha256(b"VALUE = 17\r\n").hexdigest(), "S_ACTUAL_DIGEST")

    def test_modified_literal_refused_before_compile(self):
        self.path.write_bytes(CHANGED)
        with patch.object(pinned, "compile", create=True, wraps=compile) as compiler:
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
                pinned._load(self.selected, self.name, self.path)
            compiler.assert_not_called()
        self.assertNotIn(self.name, sys.modules, "S_REFUSED_NO_MODULE")

    def test_same_buffer_executes(self):
        original = Path.read_bytes
        reads = []
        def read_then_change(path):
            body = original(path)
            if path.resolve() == self.path:
                reads.append(body)
                path.write_bytes(CHANGED)
            return body
        with patch.object(Path, "read_bytes", read_then_change):
            module = pinned._load(self.selected, self.name, self.path)
        self.assertEqual(module.VALUE, 17, "S_EXECUTES_CAPTURED_BUFFER")
        self.assertEqual(reads, [LITERAL], "S_SINGLE_READ")
        self.assertEqual(self.path.read_bytes(), CHANGED, "S_CHANGED_AFTER_READ")
        self.assertEqual(module._xiv_stitch_source_sha256,
                         hashlib.sha256(LITERAL).hexdigest(), "S_EXECUTED_DIGEST")

    def test_captured_commit_not_new_head(self):
        self.path.write_bytes(CHANGED)
        fixture_git(self.repo, "add", "--", "literal.py")
        fixture_git(self.repo, "commit", "-qm", "second benign fixture")
        self.assertNotEqual(fixture_git(self.repo, "rev-parse", "HEAD"), self.commit)
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
            pinned.read_pinned(self.selected, self.path)
        self.path.write_bytes(LITERAL)
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL, "S_CAPTURED_COMMIT")

    def test_outside_pins_refused(self):
        outside = self.root / "outside.py"
        outside.write_bytes(LITERAL)
        self.assertTrue(outside.is_file())
        with patch.object(tectonica, "git_bytes") as git_read:
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_OUTSIDE_PINS:"):
                pinned.read_pinned(self.selected, outside)
            git_read.assert_not_called()

    def test_invalid_pin_refused(self):
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_PIN_INVALID:"):
            pinned.read_pinned({"XV": (self.repo, "HEAD")}, self.path)

    def test_non_equivalent_newlines_refused(self):
        self.path.write_bytes(b"VALUE = 17\r")
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
            pinned.read_pinned(self.selected, self.path)

    def test_loader_cache_ownership(self):
        # This test owns its one cache key; both global dictionaries are restored.
        with patch.dict(pinned._LOADED), patch.dict(sys.modules):
            foreign = ModuleType(self.name)
            foreign.__file__ = str(self.path)
            foreign._xiv_stitch_source_sha256 = hashlib.sha256(LITERAL).hexdigest()
            foreign.VALUE = 23
            sys.modules[self.name] = foreign
            with self.assertRaisesRegex(tectonica.Refusal, "^PINNED_MODULE_CONFLICT:"):
                pinned._load(self.selected, self.name, self.path)
            sys.modules.pop(self.name)
            owned = pinned._load(self.selected, self.name, self.path)
            self.assertIs(pinned._load(self.selected, self.name, self.path), owned, "S_OWNED_CACHE")
            sys.modules[self.name] = foreign
            with self.assertRaisesRegex(tectonica.Refusal, "^PINNED_MODULE_CONFLICT:"):
                pinned._load(self.selected, self.name, self.path)
            sys.modules.pop(self.name)
            with self.assertRaisesRegex(tectonica.Refusal, "^PINNED_MODULE_CONFLICT:"):
                pinned._load(self.selected, self.name, self.path)
            sys.modules[self.name] = owned
            self.path.write_bytes(CHANGED)
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
                pinned._load(self.selected, self.name, self.path)

    def test_import_error_cleanup(self):
        # A trusted interpreter failure is injected; fixture source remains literal-only.
        with patch.object(pinned, "exec", create=True, side_effect=ImportError("BENIGN_STOP")):
            with self.assertRaisesRegex(ImportError, "^BENIGN_STOP$"):
                pinned._load(self.selected, self.name, self.path)
        self.assertNotIn(self.name, sys.modules, "S_FAILED_IMPORT_REMOVED")
        self.assertNotIn(self.name, pinned._LOADED, "S_FAILED_IMPORT_UNOWNED")
        self.assertEqual(pinned._load(self.selected, self.name, self.path).VALUE, 17, "S_RETRY")

    def test_entry_fresh_and_capture_is_copied(self):
        first = pinned.load_xiv_stitch(self.selected)
        second = pinned.load_xiv_stitch(self.selected)
        self.assertIsNot(first, second, "S_FRESH_ENTRY")
        self.assertEqual(first.VALUE, 17, "S_ENTRY_LITERAL")
        self.selected.clear()
        self.assertEqual(first._load(self.name, self.path).VALUE, 17, "S_CAPTURE_COPY")

    def test_entry_same_buffer_executes(self):
        original = Path.read_bytes
        reads = []
        def read_then_change(path):
            body = original(path)
            if path.resolve() == self.entry:
                reads.append(body)
                path.write_bytes(CHANGED)
            return body
        with patch.object(Path, "read_bytes", read_then_change):
            module = pinned.load_xiv_stitch(self.selected)
        self.assertEqual(module.VALUE, 17, "S_ENTRY_BUFFER")
        self.assertEqual(reads, [LITERAL], "S_ENTRY_SINGLE_READ")

    def test_certificate_uses_bound_buffer_before_replay(self):
        selected = {"Identity": (self.repo, self.commit),
                    "XIV": (self.root / "xiv", self.commit),
                    "XV": (self.root / "xv", self.commit)}
        module = SimpleNamespace(__file__="benign", _xiv_stitch_source_sha256="benign")
        # The real certificate adapter refuses: this test never accepts a fake certificate.
        module.verify_certificate = lambda value: (_ for _ in ()).throw(ValueError("BENIGN_STOP"))
        stitch = SimpleNamespace(_xiv_stitch_source_sha256="benign",
                                 load_sources=lambda *args: SimpleNamespace(provenance={}),
                                 _load=lambda *args: module)
        real_read = pinned.read_pinned
        def checked_then_change(selected, path):
            body = real_read(selected, path)
            path.write_bytes(b'{"value":23}\n')
            return body
        with patch.object(tectonica, "checked_layers", return_value=selected), \
             patch.object(pinned, "load_xiv_stitch", return_value=stitch), \
             patch.object(identity.json, "loads", wraps=identity.json.loads) as parse, \
             patch.object(pinned, "read_pinned", side_effect=checked_then_change) as read:
            with self.assertRaisesRegex(identity.Refusal, "^CERTIFICATE_REJECTED: BENIGN_STOP$"):
                identity.load_sources(self.root)
            read.assert_called_once_with(selected, self.certificate)
            parse.assert_called_once_with('{"value":17}\n')
            read.reset_mock()
            parse.reset_mock()
            self.certificate.write_bytes(b'{"value":23}\n')
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
                identity.load_sources(self.root)
            parse.assert_not_called()

    def test_missing_promisor_blob_does_not_fetch(self):
        remote = self.root / "promisor.git"
        fixture_git(self.repo, "-c", "protocol.allow=never", "-c", "protocol.file.allow=always",
                    "clone", "--bare", "--no-hardlinks", str(self.repo), str(remote))
        fetched = self.root / "fetch-requested"
        upload = self.root / "upload-pack.sh"
        upload.write_text(
            "#!/bin/sh\nprintf fetched > " + shlex.quote(fetched.as_posix()) +
            '\nexec git-upload-pack "$@"\n', encoding="utf-8", newline="\n")
        upload.chmod(0o700)
        for key, value in (
                ("protocol.allow", "never"), ("protocol.file.allow", "always"),
                ("remote.origin.url", str(remote)), ("remote.origin.promisor", "true"),
                ("remote.origin.partialclonefilter", "blob:none"),
                ("remote.origin.uploadpack", shlex.quote(upload.as_posix())),
                ("core.hooksPath", str(self.repo / ".fixture-empty-hooks")),
                ("commit.gpgsign", "false"), ("maintenance.auto", "false")):
            fixture_git(self.repo, "config", key, value)
        fixture_git(remote, "config", "uploadpack.allowFilter", "true")
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL, "S_PROMISOR_PRESENT")
        blob = fixture_git(self.repo, "rev-parse", self.commit + ":literal.py")
        object_path = self.repo / ".git/objects" / blob[:2] / blob[2:]
        object_path.chmod(0o600)
        object_path.unlink()
        refusal = ""
        try:
            pinned.read_pinned(self.selected, self.path)
        except tectonica.Refusal as exc:
            refusal = str(exc)
        self.assertFalse(fetched.exists(), "S_NO_LAZY_FETCH: promised blob requested from origin")
        self.assertRegex(refusal, "^GIT_FAILED:", "S_MISSING_BLOB_REFUSAL")

    def test_git_failure_refuses(self):
        with self.assertRaisesRegex(tectonica.Refusal, "^GIT_FAILED:"):
            pinned.read_pinned({"XV": (self.repo, "0" * 40)}, self.path)
        with patch.object(tectonica.subprocess, "run", side_effect=OSError("benign")):
            with self.assertRaisesRegex(tectonica.Refusal, "^GIT_UNAVAILABLE$"):
                tectonica.git_bytes(self.repo, "rev-parse", "HEAD")

    def test_git_environment_and_raw_bytes(self):
        env = {"GIT_DIR": "benign-invalid", "gIt_WoRk_TrEe": "benign-invalid", "KEEP_ME": "17"}
        with patch.dict(os.environ, env, clear=True), \
             patch.object(tectonica.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"17\r\n", b"")) as run:
            self.assertEqual(tectonica.git_bytes(self.repo, "cat-file", "blob", "ref"), b"17\r\n", "S_RAW_BYTES")
            command = run.call_args.args[0]
            self.assertIn("--no-replace-objects", command, "S_NO_REPLACE_OBJECTS")
            self.assertEqual(run.call_args.kwargs["env"], {"KEEP_ME": "17"}, "S_GIT_ENV_SCRUB")
        with patch.dict(os.environ, {"GIT_DIR": str(self.root / "missing")}, clear=False):
            self.assertEqual(tectonica.git(self.repo, "rev-parse", "HEAD"), self.commit, "S_REAL_GIT_SCRUB")


class VendoredSourcesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vendored-fixture-")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve() / "project"
        self.directory = self.repo / "layers/ProbeVI"
        self.path = self.directory / "harness/probe_vi.py"
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(LITERAL)
        # A different root-relative blob makes loss of the selected prefix visible.
        decoy = self.repo / "harness/probe_vi.py"
        decoy.parent.mkdir()
        decoy.write_bytes(CHANGED)
        (self.repo / "README.md").write_bytes(b"Root fixture\n")
        fixture_git(self.repo, "init", "-q")
        fixture_git(self.repo, "add", "--", "layers/ProbeVI", "harness", "README.md")
        fixture_git(self.repo, "commit", "-qm", "benign included source fixture")
        self.commit = fixture_git(self.repo, "rev-parse", "HEAD")
        self.selected = {"ProbeVI": (self.directory, self.commit)}
        self.name = "_vendored_fixture_" + self.repo.parent.name.replace("-", "_")
        self.addCleanup(pinned._LOADED.pop, self.name, None)
        self.addCleanup(sys.modules.pop, self.name, None)

    def test_exact_prefix_and_crlf(self):
        with patch.object(tectonica, "git_bytes", wraps=tectonica.git_bytes) as read:
            try:
                actual = pinned.read_pinned(self.selected, self.path)
            except Exception as exc:
                self.fail("S_VENDORED_PREFIX: " + str(exc))
            self.assertEqual(actual, LITERAL, "S_VENDORED_EXACT")
            read.assert_any_call(self.repo, "cat-file", "blob",
                                 self.commit + ":layers/ProbeVI/harness/probe_vi.py")
        self.path.write_bytes(b"VALUE = 17\r\n")
        self.assertEqual(pinned.read_pinned(self.selected, self.path), b"VALUE = 17\r\n",
                         "S_VENDORED_CRLF")
        self.assertEqual(pinned._load(self.selected, self.name, self.path).VALUE, 17,
                         "S_VENDORED_EXECUTES")

    def test_changed_source_refused(self):
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL,
                         "S_VENDORED_CONTENT_CONTROL")
        self.path.write_bytes(CHANGED)
        with patch.object(pinned, "compile", create=True, wraps=compile) as compiler:
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
                pinned._load(self.selected, self.name, self.path)
            compiler.assert_not_called()
        self.assertNotIn(self.name, sys.modules, "S_VENDORED_REFUSED_NO_MODULE")

    def test_foreign_git_root_refused(self):
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL,
                         "S_VENDORED_ROOT_CONTROL")
        with patch.object(tectonica, "git", return_value=str(self.repo.parent)), \
             patch.object(tectonica, "git_bytes") as read:
            with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_ROOT_MISMATCH:"):
                pinned.read_pinned(self.selected, self.path)
            read.assert_not_called()

    def test_selected_prefix_required(self):
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_ROOT_MISMATCH:"):
            pinned.read_pinned({"ProbeVI": (self.path.parent, self.commit)}, self.path)
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_OUTSIDE_PINS:"):
            pinned.read_pinned(self.selected, self.repo / "harness/probe_vi.py")
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_ROOT_MISMATCH:"):
            pinned.read_pinned({"XV": (self.directory, self.commit)}, self.path)

    def test_root_changes_outside_source_do_not_change_pin(self):
        (self.repo / "README.md").write_bytes(b"Other root change\n")
        fixture_git(self.repo, "update-index", "--skip-worktree", "README.md")
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL,
                         "S_VENDORED_ROOT_CHANGE_CONTROL")
        self.assertEqual(fixture_git(self.repo, "rev-parse", "HEAD"), self.commit,
                         "S_VENDORED_FIXED_COMMIT")

    def test_captured_commit_and_same_buffer(self):
        original = Path.read_bytes
        reads = []
        def read_then_change(path):
            body = original(path)
            if path.resolve() == self.path:
                reads.append(body)
                path.write_bytes(CHANGED)
            return body
        with patch.object(Path, "read_bytes", read_then_change):
            module = pinned._load(self.selected, self.name, self.path)
        self.assertEqual(module.VALUE, 17, "S_VENDORED_CAPTURED_BUFFER")
        self.assertEqual(reads, [LITERAL], "S_VENDORED_SINGLE_READ")
        fixture_git(self.repo, "add", "--", "layers/ProbeVI")
        fixture_git(self.repo, "commit", "-qm", "second benign included source fixture")
        with self.assertRaisesRegex(tectonica.Refusal, "^SOURCE_CONTENT_MISMATCH:"):
            pinned.read_pinned(self.selected, self.path)
        self.path.write_bytes(LITERAL)
        self.assertEqual(pinned.read_pinned(self.selected, self.path), LITERAL,
                         "S_VENDORED_CAPTURED_COMMIT")

    def test_foreign_cache_refused(self):
        with patch.dict(pinned._LOADED), patch.dict(sys.modules):
            foreign = ModuleType(self.name)
            foreign.__file__ = str(self.path)
            foreign._xiv_stitch_source_sha256 = hashlib.sha256(LITERAL).hexdigest()
            sys.modules[self.name] = foreign
            with self.assertRaisesRegex(tectonica.Refusal, "^PINNED_MODULE_CONFLICT:"):
                pinned._load(self.selected, self.name, self.path)
            sys.modules.pop(self.name)
            owned = pinned._load(self.selected, self.name, self.path)
            self.assertIs(pinned._load(self.selected, self.name, self.path), owned,
                          "S_VENDORED_OWNED_CACHE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
