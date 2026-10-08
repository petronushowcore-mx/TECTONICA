"""LOCAL fixed Probe VI controlled fixtures; no Graph/plant translation."""
from dataclasses import dataclass, replace
from fractions import Fraction as Q

@dataclass(frozen=True)
class Fixture:
    name: str
    a: tuple
    b: tuple
    h_rows: tuple
    x0: tuple
    controls: tuple
    u_bounds: tuple = (Q(-1), Q(1))
    h: tuple = (Q(0), Q(0))
    horizon: str = "forward-infinite"
    strategy: str = "constant supplied witnesses"


def fixtures(probe):
    base = probe.ProbeModel()
    return (
        Fixture("canonical", base.a, base.b, base.h_rows, base.x_star, base.witnesses),
        Fixture("zero", base.a, base.b, base.h_rows, base.x3_zero_probe, (base.x3_zero_u,)),
        Fixture("aligned", base.a, base.aligned_b, base.h_rows, base.x_star, (base.aligned_u,)),
    )


def report(probe, f):
    if type(f) is not Fixture:
        return {"status": "NOT_ESTABLISHED", "reason": "typed Fixture required"}
    fields = (f.a, f.b, f.h_rows, f.x0, f.controls, f.u_bounds, f.h)
    if any(type(v) is not tuple for v in fields) or any(type(v) is not tuple for v in (*f.a, *f.h_rows)):
        return {"status": "NOT_ESTABLISHED", "reason": "exact tuple data required"}
    values = (*f.b, *f.x0, *f.controls, *f.u_bounds, *f.h,
              *(v for row in (*f.a, *f.h_rows) for v in row))
    if any(type(v) is not Q for v in values):
        return {"status": "NOT_ESTABLISHED", "reason": "exact Fraction data required"}
    declared = fixtures(probe)
    if f not in declared:
        return {"status": "NOT_ESTABLISHED", "reason": "outside fixed source fixtures"}
    base = probe.ProbeModel()
    try:
        local = local_viability(probe, f)
        if local != (True, True):
            return {"status": "NOT_ESTABLISHED", "reason": "local trajectory certificate failed"}
        if f.name == "canonical":
            individual = probe.check_individual_witnesses(base)
            rate = probe.check_sum_rate(base)
            exact = probe.check_set_separation(base)
            return {"status": "PROVED_CANONICAL_OBSTRUCTION", "individual": individual,
                    "sum_rate": rate, "exact_model": exact, "local_viability": local,
                    "common_witness": None, "basis": "Probe VI primary §3 plus T4 identities; all admissible controls"}
        # T6 proves its specific stationary controls, not a generic plant theorem.
        source_controls = probe.check_negative_controls(base)
        rates = probe.rates(base, f.x0, f.controls[0], b=f.b)
        feasible = all(probe.dot(row, f.x0) + h <= 0 for row, h in zip(f.h_rows, f.h))
        if rates != (Q(0), Q(0), Q(0)) or not feasible:
            return {"status": "NOT_ESTABLISHED", "reason": "stationary shared witness not certified"}
        return {"status": "CONCRETE_COMMON_WITNESS", "u": str(f.controls[0]),
                "rates": tuple(map(str, rates)), "x0": tuple(map(str, f.x0)),
                "trajectory": "constant x(t)=x0 for every t>=0", "source_controls": source_controls, "local_viability": local}
    except probe.CheckFailure as failure:
        return {"status": "NOT_ESTABLISHED", "reason": failure.marker}

def local_viability(probe, f):
    """Compute each local certificate on this fixed catalogue, for every t>=0.

    Non-positive polynomial coefficients and zero remainder suffice here.
    These certificates establish existence, not a general viability algorithm.
    """
    model = replace(probe.ProbeModel(), a=f.a, b=f.b, x_star=f.x0)
    controls = f.controls if f.name == "canonical" else (f.controls[0],) * 2
    answers = []
    for row, offset, control in zip(f.h_rows, f.h, controls):
        coefficients, remainder = probe.constant_control_trajectory_coefficients(model, f.x0, control)
        constrained = (probe.dot(row, coefficients[0]) + offset,) + tuple(
            probe.dot(row, coefficient) for coefficient in coefficients[1:])
        answers.append(f.u_bounds[0] <= control <= f.u_bounds[1]
                       and remainder == (Q(0), Q(0), Q(0))
                       and all(coefficient <= 0 for coefficient in constrained))
    return tuple(answers)
