# Identity schedules across three layers

## Scope and limits

This composition runs exact finite examples from three pinned repositories.
Identity supplies a certificate-defined two-loop carrier and event maps; XV
supplies graph transport and the finite nesting construction; XIV evaluates
Independent Exhaustion (IE). The Identity certificate is independently replayed
before its maps, covector and initial cycle are interpreted.

The relation between schedule costs and substrate burdens is an explicit input
assignment. It is not derived from the topological maps, a physical cost law, or
an empirical identity criterion. The topology carrier and the accounting graph
are different objects. No claim is made about carrier completeness or relevance
of the supplied witness to a real system.

A nonzero final pairing is not the same as an unchanged period, survival at every
intermediate window, or a nonzero class inferred from that pairing's absence.
The whole graph cohomology class is checked separately. The IE result is the
finite boundary construction with `m_IE = 0`; positive-margin robustness, full
Regime W, physical hostability, epistemic independence and infinite continuation
are not established. The original XIV/XV limits and premises remain in
[layers/XV/INTEGRATION.md](layers/XV/INTEGRATION.md).

## Objects and correspondence

| Identity object | Connection | XV / XIV object |
|---|---|---|
| Ordered indexed edges of a two-loop carrier | Preserve vertex and edge indices | XV graph on the same carrier, with parallel loops retained |
| Signed integer cycle | Compare exact transported coefficients | XV induced pushforward; zero coefficients are omitted for comparison |
| Rational covector and cycle | Compare each window's exact period | XV pairing on the transported cycle |
| Edge images as signed paths | Substitute paths, reversing order and signs for inverse traversal | Validated composite graph map |
| One schedule window | Create one transition between new consecutive accounting states | Upper directed substrate edge |
| Sum of the window's declared channel increments | Assign that edge's burden | Prefix burden compared against Identity cumulative cost |
| Supplied positive finite capacity C | Require total upper burden strictly below C | XV construction of a lower, explicit-window substrate |
| Accounting trajectory and constructed lower | Evaluate actual imported IE functions | XIV `NESTED-BOUNDARY`, `m_IE = 0` |

The accounting states are `0, ..., number_of_windows`. Edge `(j, j+1)` accounts
for window `j`. Its cost is the sum of increments of the active channels in that
window; the first edge includes the first window's cost. Each switch follows a
window and precedes the next one. There is one more window than switch. Every
prefix is compared, including the final one.

Identity validates channel capacity, exact nonnegative costs and coverage of all
declared channels. Its `k` is the maximum number of concurrently active channels;
it is not the upper substrate capacity `C`, nor the traversal count used to
construct the lower capacity. Empty active windows and zero-cost transitions
are permitted when the complete schedule still covers all declared channels.
Accounting uses the validated, materialised windows; an omitted increment for an
active channel means zero, as it does in Identity.
Signed reverse traversals describe graph-chain transport, not permitted physical
actions on the directed accounting path.

The topology carrier has two loops with the same endpoints. It is never passed
to the XIV substrate adapter, whose representation would merge parallel edges.
The separately constructed accounting path has unique ordered edge pairs.

## Four finite examples

The maps A, B and C, initial cycle `(1,-1)` and covector `(1,0)` come from
Identity's checked certificate. Each example uses one distinct channel per
window, concurrency limit 1, window cost 1/3, and upper capacity 2.

| Event order | Period at each window | Final pairing verdict | Upper total cost | Upper slack at lower exhaustion |
|---|---|---|---|---|
| A B A B | 1, 1, 1, 1, 1 | PRESERVING | 5/3 | 1/3 |
| B C | 1, 1, 0 | ANNIHILATING | 1 | 1 |
| C B | 1, -1, -1 | PRESERVING | 1 | 1 |
| B C C | 1, 1, 0, 1 | PRESERVING | 4/3 | 2/3 |

`PRESERVING` is XV's transport-relative verdict on the supplied singleton cycle
family: its final pairing remains nonzero. It does not mean that the numeric
period is unchanged. The B C C trace returns to a nonzero pairing after an
intermediate zero; that is not uninterrupted witness survival. In all four
examples the fixed covector defines a nonzero global class on the bouquet,
including B C, whose selected transported pairing is zero.

Each schedule receives its own accounting path and lower construction. All four
produce the formal boundary IE verdict. B C and C B have identical costs at every
window but different final pairing verdicts. This demonstrates separation of the
readouts within the declared model, not statistical or causal independence in a
physical system.

## Execution and evidence

`python -B tectonica.py` first validates all three dependency gitlinks against
HEAD and their clean checkouts, then runs the existing XIV/XV construction and
its controls, followed by `identity_stitch.py`. The first failed child stops the
launch and its nonzero status is returned. `--check-only` checks dependency pins,
cleanliness and required entry files; it does not run certificate replay or the
mathematical checks. The standalone adapter also checks all pins before imports.

The adapter reports the loaded source and certificate hashes, cycle and period
traces, cumulative costs, accounting-prefix burdens, final pairing verdict,
period constancy, global-class diagnostic and IE result. Hashes identify input
bytes; they are not scientific certification or protection against concurrent
file changes. The imported XV loader rejects conflicting preloaded modules.

`python -B -m unittest -v test_tectonica test_identity_stitch` runs launch fixtures
and checks with the actual pinned dependencies. The latter include corruptions
of cycle transport, composition, period traces, survival flags, verdict labels
and accounting prefixes, plus a cancelling-path positive control. These tests
are distinct from the upstream repositories' own complete suites. Longer user
schedules can make the imported finite IE enumeration expensive; the default
examples are deliberately small. No arbitrary schedule-input CLI is provided.

## Sources

- [Identity Does Not Drift](https://doi.org/10.17605/OSF.IO/4NMTW): published
  `harness/switch_transport.py`, `emergence_verify.py` and
  `emergence_certificate.json` at the recorded dependency commit.
- [ONTOΣ XV](https://doi.org/10.17605/OSF.IO/EAUD5): `graph_hodge.py`,
  `core_reduction.py`, `nestability.py`, `xiv_stitch.py` and repository errata.
- [ONTOΣ XIV](https://doi.org/10.17605/OSF.IO/KAGMH): finite-state harness,
  robustness companion and repository errata.

The deposited scientific files and previous release tags are preserved.
