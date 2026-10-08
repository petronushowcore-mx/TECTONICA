"""Regression and targeted-mutation checks for the Probe VI certificate."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from probe_vi import (
    CheckFailure,
    ProbeModel,
    Q,
    certificate,
    check_sum_rate,
    check_set_separation,
    constant_control_trajectory_coefficients,
    dot,
    first_failure,
    vector,
)


class ProbeVICertificateTests(unittest.TestCase):
    def test_baseline_certificate_is_green(self) -> None:
        receipt = certificate()
        self.assertEqual(receipt["result"], "PASS")
        # The published convention, reported apart from the model because no
        # mutation can vary it: this asserts the receipt still declares h = 0.
        self.assertEqual(receipt["fixed_convention"]["h"], ["0", "0"])
        self.assertEqual(
            [item["id"] for item in receipt["checks"]],
            [
                "T1_ASSUMPTIONS",
                "T2_INDIVIDUAL_WITNESSES",
                "T3_SUM_RATE",
                "T4_SET_SEPARATION",
                "T5_POLYTOPIC_REACH",
                "T6_NEGATIVE_CONTROLS",
            ],
        )
        self.assertIsNone(first_failure(ProbeModel()))

    def test_each_check_rejects_its_targeted_model_mutation_first(self) -> None:
        base = ProbeModel()
        mutations = {
            "T1_ASSUMPTIONS": replace(
                base,
                a=(
                    vector(0, 0, 0),
                    vector(0, 0, 1),
                    vector(0, 0, 0),
                ),
            ),
            "T2_INDIVIDUAL_WITNESSES": replace(
                base,
                witnesses=(Q(0), Q(0)),
            ),
            "T3_SUM_RATE": replace(
                base,
                b=vector(-1, -1, 0),
                witnesses=(Q(1), Q(1)),
            ),
            "T4_SET_SEPARATION": replace(
                base,
                a=(
                    base.a[0],
                    vector(-2, 0, 1),
                    base.a[2],
                ),
            ),
            # x_star leaves the tangentiality equations but stays in both
            # hulls, so the red is the named fact and not hull retention.
            "T5_POLYTOPIC_REACH": replace(
                base,
                x_star=vector(0, 0, Q(1, 2)),
                sample_sets=tuple(
                    tuple(
                        vector(0, 0, Q(1, 2)) if point == base.x_star else point
                        for point in samples
                    )
                    for samples in base.sample_sets
                ),
            ),
            "T6_NEGATIVE_CONTROLS": replace(
                base,
                aligned_b=vector(-1, 0, 0),
            ),
        }
        for expected_marker, mutant in mutations.items():
            with self.subTest(expected_marker=expected_marker):
                self.assertEqual(first_failure(mutant), expected_marker)

        additional_teeth = {
            "T1_ZERO_CONSTRAINT_ROW": (
                "T1_ASSUMPTIONS",
                replace(base, h_rows=(vector(0, 0, 0), base.h_rows[1])),
            ),
            "T1_INTERIOR_POINT": (
                "T1_ASSUMPTIONS",
                replace(base, h_rows=(vector(-1, 0, 0), base.h_rows[1])),
            ),
            "T3_ZERO_RATE": (
                "T3_SUM_RATE",
                replace(base, x_star=vector(0, 0, 0)),
            ),
            "T2_CONSTRAINT_ROW": (
                "T2_INDIVIDUAL_WITNESSES",
                replace(
                    base,
                    h_rows=(base.h_rows[0], vector(0, 1, 1)),
                ),
            ),
            # T4 guards the presentation the derivation is stated for:
            # canonical rows, gains, caps. A scaled row is a different
            # presentation, so T4 owns this red. Note that T4 stands in
            # front of T5 for model-level changes generally - b=(2,-2,0)
            # passes T1-T3, reddens T4 on the gains, and the fact it truly
            # breaks is T5's tangentiality equation. That ordering is
            # deliberate, not coverage of T5.
            "T4_CANONICAL_ROWS": (
                "T4_SET_SEPARATION",
                replace(
                    base,
                    h_rows=(vector(2, 0, 0), base.h_rows[1]),
                ),
            ),
            "T6_ALIGNED_THIRD": (
                "T6_NEGATIVE_CONTROLS",
                replace(
                    base,
                    aligned_b=vector(-1, -1, 1),
                ),
            ),
            "T2_FULL_TRAJECTORY": (
                "T2_INDIVIDUAL_WITNESSES",
                replace(
                    base,
                    a=(
                        vector(0, 1, 1),
                        base.a[1],
                        base.a[2],
                    ),
                ),
            ),
            "T5_HULL_RETENTION": (
                "T5_POLYTOPIC_REACH",
                replace(
                    base,
                    sample_sets=(
                        (
                            vector(0, 2, 1),
                            vector(0, 1, 1),
                            vector(0, 0, 0),
                            vector(-1, 0, 1),
                        ),
                        base.sample_sets[1],
                    ),
                ),
            ),
            "T5_BOUNDARY_SAMPLES": (
                "T5_POLYTOPIC_REACH",
                replace(
                    base,
                    sample_sets=(
                        (
                            vector(0, 0, 1),
                            vector(0, 1, 1),
                            vector(0, 0, 0),
                            vector(-1, 1, 0),
                        ),
                        base.sample_sets[1],
                    ),
                ),
            ),
            "T6_X3_ZERO_SURFACE": (
                "T6_NEGATIVE_CONTROLS",
                replace(base, x3_zero_probe=vector(0, 0, 1)),
            ),
            "T6_X3_ZERO_CONTROL": (
                "T6_NEGATIVE_CONTROLS",
                replace(base, x3_zero_u=Q(1)),
            ),
        }
        for tooth, (expected_marker, mutant) in additional_teeth.items():
            with self.subTest(tooth=tooth):
                self.assertEqual(first_failure(mutant), expected_marker)

    def test_sum_rate_is_not_a_joint_viability_verdict(self) -> None:
        base = ProbeModel()
        for second_row in (vector(1, 0, 0), vector(2, 0, 0), vector(1, 0, -1)):
            with self.subTest(second_row=second_row):
                model = replace(
                    base,
                    h_rows=(vector(1, 0, 0), second_row),
                    witnesses=(Q(-1), Q(-1)),
                )
                # One control preserves both constraints for all t >= 0.
                coefficients, remainder = constant_control_trajectory_coefficients(
                    model, model.x_star, Q(-1),
                )
                self.assertEqual(remainder, vector(0, 0, 0))
                self.assertTrue(all(
                    dot(row, coefficient) <= 0
                    for row in model.h_rows for coefficient in coefficients
                ))
                # A positive coordinate-sum rate does not contradict that fact:
                # these are not the two canonical coordinate constraints.
                self.assertEqual(check_sum_rate(model), {
                    "d_dt_x1_plus_x2": "2",
                    "control_coefficient": "0",
                })
                self.assertEqual(first_failure(model), "T4_SET_SEPARATION")

    def test_derived_set_guards_check_helper_results(self) -> None:
        base = ProbeModel()

        def shifted_global_cap(model, state):
            return all(dot(row, state) <= 0 for row in model.h_rows) and state[2] <= Q(1, 2)

        regressions = (
            ("individual_caps", lambda model: (Q(2), Q(2)),
             "both individual x_3 caps must equal 1"),
            ("in_global_exact", shifted_global_cap,
             "the false-positive slab must be nonempty"),
        )
        for helper, implementation, detail in regressions:
            with self.subTest(helper=helper), patch("probe_vi." + helper, implementation):
                self.assertEqual(first_failure(base), "T4_SET_SEPARATION")
                with self.assertRaises(CheckFailure) as failure:
                    check_set_separation(base)
                self.assertEqual(failure.exception.detail, detail)

    def test_constancy_guard_and_earlier_trajectory_rejection(self) -> None:
        base = ProbeModel()
        models = (
            replace(base, a=(base.a[0], base.a[1], vector(0, 0, 1))),
            replace(base, b=vector(1, -1, 1)),
        )
        for model in models:
            with self.subTest(a=model.a, b=model.b):
                self.assertEqual(first_failure(model), "T2_INDIVIDUAL_WITNESSES")
                with self.assertRaises(CheckFailure) as failure:
                    check_set_separation(model)
                self.assertEqual(failure.exception.marker, "T4_SET_SEPARATION")
                self.assertEqual(failure.exception.detail, "x_3 must remain constant")

    def test_receipt_is_stable_across_calls(self) -> None:
        # Two in-process calls of a function built from module constants.
        # This is stability, not determinism: cross-process variation cannot
        # redden it. The shipped-receipt test below is the one that bites.
        first = json.dumps(certificate(), sort_keys=True)
        second = json.dumps(certificate(), sort_keys=True)
        self.assertEqual(first, second)

    def test_receipt_matches_the_shipped_certificate(self) -> None:
        # Bites when the computed receipt changes and certificate.json is not
        # regenerated - the case where the package would ship a receipt for a
        # run that no longer happens.
        shipped = Path(__file__).with_name("certificate.json")
        if not shipped.is_file():
            self.skipTest("certificate.json is not present in this checkout")
        on_disk = json.loads(shipped.read_text(encoding="utf-8"))
        self.assertEqual(on_disk, certificate())


if __name__ == "__main__":
    unittest.main()
