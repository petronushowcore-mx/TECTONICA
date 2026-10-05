"""Audit declared observations of finite Identity schedules with the pinned PoA API.

The target is uninterrupted preservation of one fixed covector on the certified
two-loop carrier. It is distinct from a nonzero transported pairing, viability
and identity of a physical system. See INTEGRATION.md for the finite category.
"""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import sys

import identity_stitch as identity
import tectonica

CATALOGUE = tuple("".join(word) for word in product("ABC", repeat=3))
OBSERVATIONS = ("final_cycle_cost", "period_trace_cost", "period_cost_membership")


def load_sources(root):
    """Check all declared pins and replay Identity before importing the PoA module."""
    data = identity.load_sources(root)
    path = Path(root) / "layers/PoA/harness/seam_audit.py"
    data.poa = data.stitch._load("tectonica_poa_audit", path)
    data.provenance["poa_audit"] = {
        "path": str(path.resolve()),
        "sha256": data.poa._xiv_stitch_source_sha256,
    }
    return data


def covector_pullback(data, event):
    """Pull eta back along a total graph map, on both basis cycles of the bouquet."""
    _, eta, _ = identity.certified_model(data)
    graph = data.api.graph.Graph(["v"], [("v", "v"), ("v", "v")])
    try:
        graph.check_graph_map(graph, {"v": "v"}, event)
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        raise identity.Refusal("POA_GRAPH_MAP: " + str(exc)) from exc
    return tuple(data.api.graph.period(eta, data.api.graph.induced_pushforward(event, {i: 1}))
                 for i in range(2))


def membership(data, event):
    """P_eta membership; equality of one selected pairing is insufficient."""
    _, eta, _ = identity.certified_model(data)
    return covector_pullback(data, event) == tuple(eta[i] for i in range(2))


def history_record(data, word):
    """One three-switch history, four exact cost windows, and two P_eta readouts."""
    identity.require(word in CATALOGUE, "POA_CATALOGUE_WORD")
    maps, _, _ = identity.certified_model(data)
    windows = [([j], {j: F(1, 3)}) for j in range(4)]
    row = identity.connect(data, word, windows, 4, 1, F(2))
    bits = tuple(membership(data, maps[event]) for event in word)
    composite = {0: [(0, 1)], 1: [(1, 1)]}
    for event in word:
        composite = identity.compose(composite, maps[event])
    row.update({
        "P_eta_membership": list(bits),
        "P_eta_uninterrupted": all(bits),
        "P_eta_composite_admitted": membership(data, composite),
        "composite_covector_pullback": [str(x) for x in covector_pullback(data, composite)],
    })
    return row


def observe(row, mode):
    """A declared projection; event names and other diagnostics are not included."""
    costs = tuple(row["cumulative_costs"])
    if mode == "final_cycle_cost":
        return tuple(sorted(row["cycles"][-1].items())), costs
    periods = tuple(row["periods"])
    if mode == "period_trace_cost":
        return periods, costs
    if mode == "period_cost_membership":
        return periods, costs, tuple(row["P_eta_membership"])
    raise ValueError("POA_UNKNOWN_OBSERVATION: " + str(mode))


def audit_observation(poa, rows, mode):
    """Evaluate every attained fibre of this nonempty finite catalogue.

    PoA's generic fibre functions receive event words as history identifiers.
    Its integer-defect Seam model and entropy routines are not used.
    """
    identity.require(bool(rows), "POA_EMPTY_CATALOGUE")
    words = tuple(rows)
    observation = lambda word: observe(rows[word], mode)
    target = lambda word: rows[word]["P_eta_uninterrupted"]
    groups = {}
    for word in words:
        groups.setdefault(observation(word), []).append(word)
    fibres = [{
        "observation": value,
        "histories": histories,
        "decision": poa.fibre_decision(words, observation, target, value).value,
    } for value, histories in groups.items()]
    return {
        "target": "P_eta_uninterrupted",
        "observation": mode,
        "factors_through": poa.factors_through(words, observation, target),
        "fibres": fibres,
    }


def run(data):
    """Enumerate all 27 length-three words over the certificate's A/B/C alphabet."""
    rows = {word: history_record(data, word) for word in CATALOGUE}
    return {
        "scope": "all 27 three-switch words over A/B/C on the certified two-loop carrier",
        "cost_assignment": "four windows of 1/3; distinct channels; concurrency 1; upper capacity 2",
        "commits": data.commits,
        "source_provenance": data.provenance,
        "histories": rows,
        "observations": {mode: audit_observation(data.poa, rows, mode) for mode in OBSERVATIONS},
    }


def main():
    try:
        result = run(load_sources(Path(__file__).resolve().parent))
        print(json.dumps(result, indent=2))
        print("POA_CONNECTION: PASS (27 histories; three declared observation audits)")
        return 0
    except (identity.Refusal, tectonica.Refusal, OSError, ValueError) as exc:
        print("POA_CONNECTION: REFUSED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
