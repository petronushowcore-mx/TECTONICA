"""Execute dependency buffers bound to commits captured by checked_layers.

The root package, Python and Git are trusted. Checkout status is still checked;
this additional check binds each buffer actually consumed to its captured pin.
Only exact bytes and whole LF-to-CRLF conversion of LF text are equivalent.
"""
import hashlib
from pathlib import Path
import re
import sys
from types import ModuleType

import tectonica

# Only modules loaded here can satisfy a subsequent cache lookup.
_LOADED = {}


def read_pinned(selected, path):
    """Read once, compare to the captured commit's blob, return that same buffer."""
    path = Path(path).resolve()
    matches = []
    for directory, revision in selected.values():
        directory = Path(directory).resolve()
        try:
            relative = path.relative_to(directory)
        except ValueError:
            continue
        if relative.parts:
            matches.append((directory, revision, relative.as_posix()))
    if len(matches) != 1:
        raise tectonica.Refusal("SOURCE_OUTSIDE_PINS: " + str(path))
    directory, revision, relative = matches[0]
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise tectonica.Refusal("SOURCE_PIN_INVALID: " + str(path))
    actual = path.read_bytes()
    blob = tectonica.git_bytes(directory, "cat-file", "blob", revision + ":" + relative)
    crlf = b"\r" not in blob and b"\0" not in blob and actual == blob.replace(b"\n", b"\r\n")
    if actual != blob and not crlf:
        raise tectonica.Refusal("SOURCE_CONTENT_MISMATCH: " + str(path))
    return actual


def _load(selected, name, path):
    path = Path(path).resolve()
    body = read_pinned(selected, path)
    digest = hashlib.sha256(body).hexdigest()
    cached = _LOADED.get(name)
    if cached is not None or name in sys.modules:
        if (cached is None or sys.modules.get(name) is not cached[0]
                or cached[1:] != (path, digest)
                or getattr(cached[0], "__file__", None) != str(path)
                or getattr(cached[0], "_xiv_stitch_source_sha256", None) != digest):
            raise tectonica.Refusal("PINNED_MODULE_CONFLICT: " + name)
        return cached[0]
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    try:
        exec(compile(body, str(path), "exec"), module.__dict__)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    module._xiv_stitch_source_sha256 = digest
    _LOADED[name] = (module, path, digest)
    return module


def load_xiv_stitch(selected):
    """Give this invocation a fresh pinned entry module and its bound loader."""
    selected = {name: (Path(directory).resolve(), revision)
                for name, (directory, revision) in selected.items()}
    path = selected["XV"][0] / "harness/xiv_stitch.py"
    body = read_pinned(selected, path)
    stitch = ModuleType("_tectonica_xiv_stitch")
    stitch.__file__ = str(path)
    exec(compile(body, str(path), "exec"), stitch.__dict__)
    stitch._xiv_stitch_source_sha256 = hashlib.sha256(body).hexdigest()
    stitch._load = lambda name, source: _load(selected, name, source)
    return stitch


def main():
    try:
        selected = tectonica.checked_layers(Path(__file__).resolve().parent)
        stitch = load_xiv_stitch(selected)
        return stitch.main(["--xiv-root", str(selected["XIV"][0]),
                            "--xv-root", str(selected["XV"][0]), "--teeth"])
    except (tectonica.Refusal, OSError, ValueError) as exc:
        print("PINNED_SOURCES: REFUSED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
