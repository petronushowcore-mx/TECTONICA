"""Common admissible control on three fixed source fixtures and their observations."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import tectonica
import pinned_sources
import controlled_adapter as adapter

OBSERVATIONS = ("local_viability", "full_profile")
EXPECTED_CHECKS = 9

def load(selected):
    if "ProbeVI" not in selected:
        raise tectonica.Refusal("PIN_REQUIRED: ProbeVI")
    return pinned_sources._load(selected, "tectonica_probe_vi",
                                Path(selected["ProbeVI"][0]) / "harness/probe_vi.py")

def load_poa(selected):
    return pinned_sources._load(selected, "tectonica_common_control_poa",
                                Path(selected["PoA"][0]) / "harness/seam_audit.py")

def catalogue(probe):
    rows = {}
    for fixture in adapter.fixtures(probe):
        proof = adapter.report(probe, fixture)

        rows[fixture.name] = {"fixture": fixture, "proof": proof}
    return rows

def target(row):
    status = row["proof"]["status"]
    if status == "CONCRETE_COMMON_WITNESS":
        return True
    if status == "PROVED_CANONICAL_OBSTRUCTION":
        return False
    raise tectonica.Refusal("COMMON_CONTROL_TARGET_UNESTABLISHED")

def observe(row, mode):
    f = row["fixture"]
    if mode == "local_viability":
        return row["proof"]["local_viability"]
    if mode == "full_profile":
        return (f.a, f.b, f.h_rows, f.h, f.x0, f.u_bounds, f.horizon, f.strategy, f.controls)
    raise ValueError("COMMON_CONTROL_UNKNOWN_OBSERVATION: " + str(mode))

def audit(poa, rows, mode):
    names = tuple(rows)
    if not names:
        raise tectonica.Refusal("COMMON_CONTROL_EMPTY_CATALOGUE")
    # A bijective index encoding into PoA's declared History domain.
    # The loop, zero defect and admitted flag carry no plant/time semantics.
    decode = {(poa.Seam(name, "catalogue", "catalogue", 0, True),): name for name in names}
    histories = tuple(decode)
    observation = lambda history: observe(rows[decode[history]], mode)
    predicate = lambda history: target(rows[decode[history]])
    groups = {}
    for history in histories:
        groups.setdefault(observation(history), []).append(decode[history])
    return {"factors_through": poa.factors_through(histories, observation, predicate),
            "fibres": [{"observation": value, "fixtures": members,
                        "decision": poa.fibre_decision(histories, observation, predicate, value).value}
                       for value, members in groups.items()]}

def verify(probe, poa, rows):
    checks = []
    def check(condition, marker):
        if not condition:
            raise tectonica.Refusal(marker)
        checks.append(marker)
    check(tuple(rows) == ("canonical", "zero", "aligned"), "C_CATALOGUE")
    check(all(row["proof"]["status"] in ("PROVED_CANONICAL_OBSTRUCTION", "CONCRETE_COMMON_WITNESS")
              for row in rows.values()), "C_CERTIFIED_CATALOGUE")
    check(adapter.report(probe, replace(adapter.fixtures(probe)[0], x0=(adapter.Q(0),)*3))
          ["status"] == "NOT_ESTABLISHED", "C_UNSUPPORTED")
    check(tuple(target(row) for row in rows.values()) == (False, True, True), "C_COMMON_TARGET")
    check(tuple(observe(row, "local_viability") for row in rows.values())
          == ((True, True),)*3, "C_LOCAL_CERTIFICATES")
    check(rows["zero"]["proof"]["u"] == "0" and rows["aligned"]["proof"]["u"] == "1"
          and all(rows[name]["proof"]["rates"] == ("0", "0", "0")
                  for name in ("zero", "aligned")), "C_STATIONARY_WITNESSES")
    local = audit(poa, rows, "local_viability")
    check(local["factors_through"] is False and len(local["fibres"]) == 1
          and local["fibres"][0]["decision"] == "insufficient observation", "C_LOCAL_FIBRE")
    full = audit(poa, rows, "full_profile")
    check(full["factors_through"] is True and len(full["fibres"]) == 3
          and tuple(fibre["decision"] for fibre in full["fibres"]) == ("reject", "admit", "admit"),
          "C_FULL_PROFILE")
    try:
        target({"proof": {"status": "NOT_ESTABLISHED"}})
    except tectonica.Refusal as error:
        rejected = str(error) == "COMMON_CONTROL_TARGET_UNESTABLISHED"
    else:
        rejected = False
    check(rejected, "C_BOOLEAN_DOMAIN")
    if len(checks) != EXPECTED_CHECKS:
        raise tectonica.Refusal("C_EXECUTED_COUNT")
    return checks

def run(selected):
    probe, poa = load(selected), load_poa(selected)
    rows = catalogue(probe)
    checks = verify(probe, poa, rows)
    return {"scope": "three fixed source fixtures; continuous t>=0",
            "commits": {name: revision for name, (_, revision) in selected.items()},
            "source_provenance": {
                "probe": {"path": probe.__file__, "sha256": probe._xiv_stitch_source_sha256},
                "poa": {"path": poa.__file__, "sha256": poa._xiv_stitch_source_sha256}},
            "fixtures": {name: row["proof"] for name, row in rows.items()},
            "observations": {mode: audit(poa, rows, mode) for mode in OBSERVATIONS},
            "full_profile_basis": "informational sufficiency by construction on this catalogue",
            "checks": checks, "check_count": len(checks)}

def encode_exact(value):
    if type(value) is adapter.Q:
        return str(value)
    raise TypeError("COMMON_CONTROL_REPORT_TYPE: " + type(value).__name__)

def main():
    try:
        selected = tectonica.checked_layers(Path(__file__).resolve().parent)
        result = run(selected)
        print(json.dumps(result, indent=2, default=encode_exact))
        print("COMMON_CONTROL_CONNECTION: PASS")
        return 0
    except (tectonica.Refusal, OSError, ValueError, TypeError) as error:
        print("COMMON_CONTROL_CONNECTION: REFUSED " + str(error), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())



