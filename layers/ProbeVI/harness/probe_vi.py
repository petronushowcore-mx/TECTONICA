"""Exact executable certificate for NC2.5 Empirical Probe VI."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import sys
from typing import Callable


Q = Fraction
Vector = tuple[Q, Q, Q]
Matrix = tuple[Vector, Vector, Vector]
Rows = tuple[Vector, ...]
SampleSet = tuple[Vector, ...]


def vector(a: int, b: int, c: int) -> Vector:
    return (Q(a), Q(b), Q(c))


A_BASE: Matrix = (
    vector(0, 0, 1),
    vector(0, 0, 1),
    vector(0, 0, 0),
)
B_BASE: Vector = vector(1, -1, 0)
H_BASE: Rows = (vector(1, 0, 0), vector(0, 1, 0))
X_STAR: Vector = vector(0, 0, 1)
S1_BASE: SampleSet = (
    vector(0, 0, 1),
    vector(0, 1, 1),
    vector(0, 0, 0),
    vector(-1, 0, 1),
)
S2_BASE: SampleSet = (
    vector(0, 0, 1),
    vector(1, 0, 1),
    vector(0, 0, 0),
    vector(0, -1, 1),
)


@dataclass(frozen=True)
class ProbeModel:
    a: Matrix = A_BASE
    b: Vector = B_BASE
    h_rows: Rows = H_BASE
    witnesses: tuple[Q, Q] = (Q(-1), Q(1))
    x_star: Vector = X_STAR
    sample_sets: tuple[SampleSet, SampleSet] = (S1_BASE, S2_BASE)
    x3_zero_probe: Vector = vector(0, -1, 0)
    x3_zero_u: Q = Q(0)
    aligned_b: Vector = vector(-1, -1, 0)
    aligned_u: Q = Q(1)


class CheckFailure(AssertionError):
    def __init__(self, marker: str, detail: str) -> None:
        super().__init__(f"{marker}: {detail}")
        self.marker = marker
        self.detail = detail


def dot(left: Vector, right: Vector) -> Q:
    return sum((x * y for x, y in zip(left, right)), Q(0))


def mat_vec(matrix: Matrix, value: Vector) -> Vector:
    return tuple(dot(row, value) for row in matrix)  # type: ignore[return-value]


def row_mat(row: Vector, matrix: Matrix) -> Vector:
    return tuple(
        sum((row[k] * matrix[k][j] for k in range(3)), Q(0))
        for j in range(3)
    )  # type: ignore[return-value]


def subtract(left: Vector, right: Vector) -> Vector:
    return tuple(x - y for x, y in zip(left, right))  # type: ignore[return-value]


def scale(value: Vector, factor: Q) -> Vector:
    return tuple(factor * item for item in value)  # type: ignore[return-value]


def rank(rows: Rows) -> int:
    work = [list(row) for row in rows]
    pivot_row = 0
    width = len(work[0]) if work else 0
    for column in range(width):
        pivot = next(
            (index for index in range(pivot_row, len(work)) if work[index][column]),
            None,
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        work[pivot_row] = [value / pivot_value for value in work[pivot_row]]
        for index, row in enumerate(work):
            if index == pivot_row or not row[column]:
                continue
            factor = row[column]
            work[index] = [
                value - factor * base
                for value, base in zip(row, work[pivot_row])
            ]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def rates(
    model: ProbeModel,
    state: Vector,
    control: Q,
    *,
    b: Vector | None = None,
) -> Vector:
    drift = mat_vec(model.a, state)
    input_vector = model.b if b is None else b
    return tuple(
        drift[index] + input_vector[index] * control for index in range(3)
    )  # type: ignore[return-value]


def ensure(condition: bool, marker: str, detail: str) -> None:
    if not condition:
        raise CheckFailure(marker, detail)


def affine_rank(points: tuple[Vector, ...]) -> int:
    anchor = points[0]
    return rank(tuple(subtract(point, anchor) for point in points[1:]))


def constant_control_trajectory_coefficients(
    model: ProbeModel,
    state: Vector,
    control: Q,
) -> tuple[tuple[Vector, Vector, Vector, Vector], Vector]:
    velocity = rates(model, state, control)
    acceleration = mat_vec(model.a, velocity)
    jerk = mat_vec(model.a, acceleration)
    remainder = mat_vec(model.a, jerk)
    coefficients = (
        state,
        velocity,
        scale(acceleration, Q(1, 2)),
        scale(jerk, Q(1, 6)),
    )
    return coefficients, remainder


def individual_caps(model: ProbeModel) -> tuple[Q, ...]:
    endpoints = (Q(-1), Q(1))
    return tuple(
        -min(dot(row, model.b) * control for control in endpoints)
        for row in model.h_rows
    )  # type: ignore[return-value]


def in_individual(model: ProbeModel, index: int, state: Vector) -> bool:
    caps = individual_caps(model)
    return dot(model.h_rows[index], state) <= 0 and state[2] <= caps[index]


def on_individual_boundary(model: ProbeModel, index: int, state: Vector) -> bool:
    caps = individual_caps(model)
    return in_individual(model, index, state) and (
        dot(model.h_rows[index], state) == 0 or state[2] == caps[index]
    )


def in_global_exact(model: ProbeModel, state: Vector) -> bool:
    return (
        all(dot(row, state) <= 0 for row in model.h_rows)
        and state[2] <= 0
    )


def check_assumptions(model: ProbeModel) -> dict[str, object]:
    marker = "T1_ASSUMPTIONS"
    ensure(all(any(value for value in row) for row in model.h_rows), marker, "H_i must be nonzero")
    interior = vector(-1, -1, 0)
    # Nonemptiness of the interior in general is a feasibility question this
    # harness does not solve; what is verified is that the recorded point is
    # strictly feasible, which exhibits a nonempty interior for THIS G.
    ensure(all(dot(row, interior) < 0 for row in model.h_rows), marker,
           "the recorded interior point must be strictly feasible")
    stacked_ranks = tuple(
        rank((row, row_mat(row, model.a))) for row in model.h_rows
    )
    ensure(stacked_ranks == (2, 2), marker, "(A2) requires both stacked ranks to equal 2")
    return {
        "stacked_ranks": list(stacked_ranks),
        "kernel_dimensions": [3 - value for value in stacked_ranks],
    }


def check_individual_witnesses(model: ProbeModel) -> dict[str, object]:
    marker = "T2_INDIVIDUAL_WITNESSES"
    trajectories = []
    for index, control in enumerate(model.witnesses):
        ensure(Q(-1) <= control <= Q(1), marker, f"u_{index + 1} must lie in U")
        coefficients, remainder = constant_control_trajectory_coefficients(
            model,
            model.x_star,
            control,
        )
        ensure(
            remainder == vector(0, 0, 0),
            marker,
            f"u_{index + 1} needs a terminating exact trajectory certificate",
        )
        ensure(
            all(dot(model.h_rows[index], coefficient) <= 0 for coefficient in coefficients),
            marker,
            f"the coefficients of H_{index + 1} x(t) must be non-positive, "
            f"which is sufficient for constraint {index + 1} to hold for all t >= 0",
        )
        trajectories.append([[str(value) for value in row] for row in coefficients])
    return {
        "u_1": str(model.witnesses[0]),
        "u_2": str(model.witnesses[1]),
        "trajectory_coefficients": trajectories,
    }


def check_sum_rate(model: ProbeModel) -> dict[str, object]:
    marker = "T3_SUM_RATE"
    # This is a local rate calculation, independent of the constraint rows.
    # The exact-model identities in check_set_separation are also needed
    # to turn it into an infinite-horizon common-control obstruction.
    summed_a = tuple(model.a[0][j] + model.a[1][j] for j in range(3))
    summed_b = model.b[0] + model.b[1]
    sum_rate = dot(summed_a, model.x_star)
    ensure(summed_b == 0, marker, "the sum rate must be independent of control")
    ensure(sum_rate > 0, marker, "x_1+x_2 must increase at x_star")
    return {
        "d_dt_x1_plus_x2": str(sum_rate),
        "control_coefficient": str(summed_b),
    }


def check_set_separation(model: ProbeModel) -> dict[str, object]:
    marker = "T4_SET_SEPARATION"
    expected_drift = vector(0, 0, 1)
    drift_rows = tuple(row_mat(row, model.a) for row in model.h_rows)
    input_gains = tuple(dot(row, model.b) for row in model.h_rows)
    ensure(
        model.h_rows == H_BASE,
        marker,
        "the exact-set derivation requires the two canonical constraints",
    )
    ensure(
        drift_rows == (expected_drift, expected_drift),
        marker,
        "both constrained drifts must equal x_3",
    )
    ensure(input_gains == (Q(1), Q(-1)), marker, "the input gains must be +1 and -1")
    # The tests also call this guard directly: changing a[2] to (0,0,1)
    # or b[2] to 1 already fails the earlier trajectory check in the full
    # certificate. Those two examples do not isolate this guard there.
    ensure(
        model.a[2] == vector(0, 0, 0) and model.b[2] == 0,
        marker,
        "x_3 must remain constant",
    )
    caps = individual_caps(model)
    # The gains imply these caps mathematically; this also checks that the
    # helper computes that consequence correctly.
    ensure(caps == (Q(1), Q(1)), marker, "both individual x_3 caps must equal 1")
    ensure(
        in_individual(model, 0, model.x_star)
        and in_individual(model, 1, model.x_star),
        marker,
        "x_star must lie in both individual admissible sets",
    )
    ensure(not in_global_exact(model, model.x_star), marker,
           "x_star must be outside the global set as the helper computes it")
    # An independently specified point checks the set-membership helpers.
    slab_point = (Q(-1), Q(-1), Q(1, 2))
    ensure(
        in_individual(model, 0, slab_point)
        and in_individual(model, 1, slab_point)
        and not in_global_exact(model, slab_point),
        marker,
        "the false-positive slab must be nonempty",
    )
    return {
        "constraint_drift_rows": [[str(value) for value in row] for row in drift_rows],
        "input_gains": [str(value) for value in input_gains],
        "individual_caps": [str(value) for value in caps],
        "global_cap": "0",
        "witness_point": [str(value) for value in model.x_star],
    }


def check_polytopic_reach(model: ProbeModel) -> dict[str, object]:
    marker = "T5_POLYTOPIC_REACH"
    endpoints = (Q(-1), Q(1))

    for row in model.h_rows:
        lhs_boundary = dot(row, model.x_star)
        lhs_tangent = dot(row_mat(row, model.a), model.x_star)
        rhs_tangent = -min(dot(row, model.b) * control for control in endpoints)
        ensure(lhs_boundary == 0, marker, "x_star must lie on each individual constraint boundary")
        ensure(lhs_tangent == rhs_tangent, marker, "x_star must satisfy each tangentiality equation")

    s1, s2 = model.sample_sets
    ensure(all(in_individual(model, 0, point) for point in s1), marker, "S_1 must be individually admissible")
    ensure(all(in_individual(model, 1, point) for point in s2), marker, "S_2 must be individually admissible")
    ensure(
        all(on_individual_boundary(model, 0, point) for point in s1)
        and all(on_individual_boundary(model, 1, point) for point in s2),
        marker,
        "every sample must lie on its individual admissible-set boundary",
    )
    ensure(affine_rank(s1) == 3 and affine_rank(s2) == 3, marker, "both hulls must be full-dimensional")
    # vertex membership, which implies hull membership; the message says the
    # narrower thing the predicate actually tests
    ensure(model.x_star in s1 and model.x_star in s2, marker,
           "x_star must be among the boundary samples of both sample sets")
    return {
        "tangentiality_point": [str(value) for value in model.x_star],
        "affine_ranks": [affine_rank(s1), affine_rank(s2)],
        "boundary_sample_counts": [len(s1), len(s2)],
    }


def check_negative_controls(model: ProbeModel) -> dict[str, object]:
    marker = "T6_NEGATIVE_CONTROLS"
    zero = model.x3_zero_probe
    zero_rates = rates(model, zero, model.x3_zero_u)
    ensure(zero[0] <= 0 and zero[1] <= 0 and zero[2] == 0, marker, "the negative-control state must lie on x_3=0 inside G")
    # Same standard as the aligned branch below. Two non-positive components at
    # one instant do not certify an infinite horizon; the whole vector vanishing
    # does, and only because the control is constant and the state is therefore
    # stationary - a state that does not move cannot acquire new rates. That is
    # why an instant suffices here and would not for a time-varying control.
    ensure(Q(-1) <= model.x3_zero_u <= Q(1), marker,
           "the x_3=0 shared control must lie in U")
    ensure(zero_rates == vector(0, 0, 0), marker,
           "the x_3=0 control must hold every component")
    aligned_rates = rates(
        model,
        model.x_star,
        model.aligned_u,
        b=model.aligned_b,
    )
    ensure(Q(-1) <= model.aligned_u <= Q(1), marker,
           "the aligned actuator's shared control must lie in U")
    # Non-positive constrained rates at one instant do not give an
    # infinite-horizon shared witness: a rising third component makes the
    # constrained rates positive a moment later. The whole vector vanishing
    # does, because the state is then stationary under this constant control
    # and its rates cannot change.
    ensure(
        aligned_rates == vector(0, 0, 0),
        marker,
        "the aligned actuator must admit one shared control holding every component",
    )
    return {
        "x3_zero_probe": [str(value) for value in zero],
        "x3_zero_shared_u": str(model.x3_zero_u),
        "aligned_actuator_shared_u": str(model.aligned_u),
    }


CHECKS: tuple[tuple[str, Callable[[ProbeModel], dict[str, object]]], ...] = (
    ("T1_ASSUMPTIONS", check_assumptions),
    ("T2_INDIVIDUAL_WITNESSES", check_individual_witnesses),
    ("T3_SUM_RATE", check_sum_rate),
    ("T4_SET_SEPARATION", check_set_separation),
    ("T5_POLYTOPIC_REACH", check_polytopic_reach),
    ("T6_NEGATIVE_CONTROLS", check_negative_controls),
)


def first_failure(model: ProbeModel) -> str | None:
    for marker, check in CHECKS:
        try:
            check(model)
        except CheckFailure as failure:
            ensure(failure.marker == marker, marker, "a check emitted the wrong marker")
            return failure.marker
    return None


def certificate(model: ProbeModel | None = None) -> dict[str, object]:
    active = ProbeModel() if model is None else model
    checks = []
    for marker, check in CHECKS:
        evidence = check(active)
        checks.append({"id": marker, "status": "PASS", "evidence": evidence})
    return {
        "probe": "NC2.5 Empirical Probe VI",
        "result": "PASS",
        "claim": "x_star is in A_1 intersection A_2 but not in A",
        "model": {
            "A": [[str(value) for value in row] for row in active.a],
            "B": [str(value) for value in active.b],
            "H": [[str(value) for value in row] for row in active.h_rows],
            "x_star": [str(value) for value in active.x_star],
        },
        # Literals of the published convention, not fields of ProbeModel:
        # no mutation can change them, so they are reported apart from the
        # model block whose entries do vary.
        "fixed_convention": {
            "h": ["0", "0"],
            "U": ["-1", "1"],
        },
        "exact_sets": {
            "A_1": "x1 <= 0 and x3 <= 1",
            "A_2": "x2 <= 0 and x3 <= 1",
            "A": "x1 <= 0 and x2 <= 0 and x3 <= 0",
        },
        "checks": checks,
    }


def main(argv: list[str]) -> int:
    # --json explicitly selects the default output format.
    if argv not in ([], ["--json"]):
        print("usage: python probe_vi.py [--json]", file=sys.stderr)
        return 2
    try:
        receipt = certificate()
    except CheckFailure as failure:
        print(
            json.dumps(
                {
                    "probe": "NC2.5 Empirical Probe VI",
                    "result": "FAIL",
                    "first_red": failure.marker,
                    "detail": failure.detail,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
