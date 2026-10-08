"""Double Fibre verification of declared finite PoA27 observations.

A singleton criterion preserves the previous uninterrupted-eta question. The
second declaration compares two existing criteria; it does not discover an
unknown policy of a physical system. Refinement is informational only.
"""
import json
from pathlib import Path
from types import MappingProxyType

import poa_stitch as poa
import tectonica

BASELINE = ("uninterrupted",)
DECLARED_COMPARISON = ("uninterrupted", "composite")
FIELDS = {"uninterrupted": "P_eta_uninterrupted",
          "composite": "P_eta_composite_admitted"}


def require_df_pin(data):
    """Require a declared DF dependency; the existing loader checks its bytes."""
    if "DoubleFibre" not in data.commits:
        raise tectonica.Refusal("PIN_REQUIRED: DoubleFibre")


def load_sources(root):
    """Use the existing captured-byte dependency loader, with no local fallback."""
    data = poa.load_sources(root)
    require_df_pin(data)
    path = Path(root) / "layers/DoubleFibre/harness/double_fibre_audit.py"
    data.double_fibre = data.stitch._load("tectonica_double_fibre_audit", path)
    data.provenance["double_fibre_audit"] = {
        "path": str(path), "sha256": data.double_fibre._xiv_stitch_source_sha256}
    return data


def capture(data):
    """Compute the current 27 histories and bind the actual declared carrier."""
    maps, eta, _ = poa.identity.certified_model(data)
    descriptor = {
        "class": "PoA27", "commits": data.commits, "maps": maps,
        "eta": {str(i): str(x) for i, x in eta.items()}, "alphabet": "ABC",
        "word_length": 3, "cost_windows": ["1/3"] * 4,
        "concurrency": 1, "upper_capacity": "2"}
    model = json.dumps(descriptor, sort_keys=True, separators=(",", ":"))
    result = poa.run(data)
    rows = {word: {
        "observations": {mode: poa.observe(row, mode) for mode in poa.OBSERVATIONS},
        "uninterrupted": int(row["P_eta_uninterrupted"]),
        "composite": int(row["P_eta_composite_admitted"]),
        "membership": tuple(row["P_eta_membership"]),
        "composite_pullback": tuple(row["composite_covector_pullback"])}
        for word, row in result["histories"].items()}
    return {"D": model, "rows": rows, "commits": dict(data.commits),
            "source_provenance": result["source_provenance"]}


def declare(snapshot, selectors=BASELINE):
    """Fix H, A, product compatibility and total binary criteria before scoring."""
    names = tuple(selectors)  # Declared comparison, independent of scores.
    if names not in (BASELINE, DECLARED_COMPARISON):
        raise ValueError("DF_DECLARED_FAMILY")
    rows = snapshot["rows"]
    if set(rows) != set(poa.CATALOGUE):
        raise ValueError("DF_COMPLETE_POA_CATALOGUE")
    if type(snapshot["D"]) is not str or not snapshot["D"]:
        raise ValueError("DF_MODEL_REQUIRED")
    sealed = {}
    for word in poa.CATALOGUE:
        row = rows[word]
        if any(type(row[name]) is not int or row[name] not in (0, 1)
               for name in FIELDS):
            raise ValueError("DF_TOTAL_BINARY_CRITERIA")
        observations = {mode: row["observations"][mode] for mode in poa.OBSERVATIONS}
        for value in observations.values():
            hash(value)
        sealed[word] = MappingProxyType({
            "observations": MappingProxyType(observations),
            "uninterrupted": row["uninterrupted"], "composite": row["composite"]})
    model = snapshot["D"]
    histories = tuple(poa.CATALOGUE)
    worlds = tuple((model, word, name) for word in histories for name in names)
    return MappingProxyType({"D": model, "histories": histories, "selectors": names,
                             "worlds": worlds, "rows": MappingProxyType(sealed)})


def visible(declaration, world, mode):
    """V(D,h,alpha) literally retains D and uses the existing PoA projection."""
    model, word, _ = world
    return model, declaration["rows"][word]["observations"][mode]


def target(declaration, world):
    """J_Adm=alpha(h) in the declared comparison; admit names that criterion."""
    _, word, selector = world
    return declaration["rows"][word][selector]


def audit(declaration, df, mode):
    """Apply the source's generic callbacks to every attained current fibre."""
    worlds = declaration["worlds"]
    obs = lambda world: visible(declaration, world, mode)
    value = lambda world: target(declaration, world)
    attained = tuple(dict.fromkeys(obs(world) for world in worlds))
    refined = df.least_refinement(obs, value)
    fibres = [{"visible": y, "worlds": df.double_fibre(worlds, obs, y),
               "verdict": df.trichotomy(worlds, obs, value, y)} for y in attained]
    witnesses = tuple((first, second) for i, first in enumerate(worlds)
                      for second in worlds[i + 1:]
                      if first[1] == second[1] and first[2] != second[2]
                      and obs(first) == obs(second) and value(first) != value(second))
    return {"mode": mode, "factors_through": df.factors_through(worlds, obs, value),
            "fibres": fibres, "selector_only_witnesses": witnesses,
            "least_refinement": tuple(refined(world) for world in worlds),
            "refined_factors_through": df.factors_through(worlds, refined, value)}


def run(data, df=None):
    """Keep the singleton baseline separate from the declared two-criterion class."""
    source = data.double_fibre if df is None else df
    snapshot = capture(data)
    declarations = (("baseline", BASELINE),
                    ("declared_comparison", DECLARED_COMPARISON))
    return {label: {"selectors": names, "target": "alpha(h)",
                   "observations": {mode: audit(declare(snapshot, names), source, mode)
                                    for mode in poa.OBSERVATIONS}}
            for label, names in declarations}


def main():
    """Run the declared finite comparison after checking all dependency pins."""
    import sys
    try:
        data = load_sources(Path(__file__).resolve().parent)
        result = {"scope": "declared PoA27; informational verification only",
                  "commits": dict(data.commits), "source_provenance": data.provenance,
                  "results": run(data)}
        print(json.dumps(result, indent=2))
        print("DOUBLE_FIBRE_CONNECTION: PASS")
        return 0
    except (tectonica.Refusal, OSError, ValueError, TypeError) as error:
        print("DOUBLE_FIBRE_CONNECTION: REFUSED " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
