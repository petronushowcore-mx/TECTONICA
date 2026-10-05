# Identity schedules and observations across five layers

## Scope and limits

This composition runs exact finite examples from five pinned repositories.
Identity supplies a certificate-defined two-loop carrier and event maps; XV
supplies graph transport and the finite nesting construction; XIV evaluates
Independent Exhaustion (IE). Physics of Abstraction (PoA) supplies generic
factorisation and observation-fibre functions. The Identity certificate is
independently replayed before its maps, covector and initial cycle are interpreted.

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

The added PoA target is uninterrupted preservation of the fixed covector on this
carrier. It is separate from viability, a selected cycle's pairing and identity
of a physical system. Its observation conclusions are relative to the declared
27-history catalogue and named projections. The full output is richer than those
projections. The composition does not enforce a process, API or security boundary
between an acting caller and the observation functions. The PoA audit does not
instantiate PoA's scalar integer-defect model or compute entropy.

Finite boundary recomposition is a separate endpoint/horizon/budget example.
Its ordered window spans are auxiliary declared data, not a duration field in
XIV Sub. A folded macro-edge can retain several windows. This operation does
not establish a new Identity certificate or compatibility of shared controls.

The finite Severance catalogue is a separate static audit on the same accounting
carrier. It computes posterior entropy only over its declared finite comparison
classes. Its deletions are changes to a finite model, not physical deletion or
preservation of a whole system.

Person’s finite budget functions interpret complete selected routes at fixed
positive capacity with nonnegative exact costs. Prefix budgets, final survival,
whole survival and first crossing are separate reports. Final and whole
survival are equivalent within these assumptions. The supplied integer spans
are auxiliary coordinates, not physical duration; moral status and whole-system
identity are not established.

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

## PoA: what can an observation determine?

### Finite category and preservation criterion

Fix the certificate's two-loop carrier `M`. Objects are `(t,M)` for
`t = 0,1,2,3`. For `s < t`, arrows from `(s,M)` to `(t,M)` are all words
of length `t-s` over A/B/C. The empty word at each object is its identity; there
are no backward arrows. Composition concatenates words in chronological order.
Thus the category is finite, composition is associative and every non-identity
arrow strictly advances time, as required by PoA Definition 2.1.

Each word acts by the corresponding composite graph transport. Distinct temporal
arrows may have the same transport: A A and C C each induce the identity graph
map, but advance time by two steps and are not temporal identity arrows.

Write `T_f` for the induced map on the two-dimensional cycle space and
`eta = (1,0)` for the fixed covector. Define `P_eta` by
`f in P_eta iff eta T_f = eta`. The adapter validates a total graph map before
evaluating this equality on both basis cycles. Testing just the initial cycle,
one basis vector or a final nonzero pairing would be a different criterion.

This gives a wide subcategory in the sense of PoA Definition 2.3: every identity
fixes `eta`, and if `f` and `g` fix it, then
`eta T_(g o f) = eta T_g T_f = eta T_f = eta`.
For the certificate maps, the pullbacks are `(1,0)` for A and B and
`(0,1)` for C. Membership is determined by graph transport independently of
costs and the chosen observation.

### Catalogue, target and counterexamples

The audit catalogue `H` consists of all 27 words with exactly three switches,
viewed as elementary histories from `(0,M)` to `(3,M)`. It is not the set of
all arrows of the category. Each history has four windows, with one distinct
channel per window, concurrency limit 1 and cost 1/3 per window. Its upper
capacity is 2, total cost is 4/3 and upper slack at lower exhaustion is 2/3.
Every history receives the same kind of finite boundary IE construction.

The target `J(h)`, printed as `P_eta_uninterrupted`, is true exactly when
all three elementary maps lie in `P_eta` (PoA Definition 2.4). The separate
`P_eta_composite_admitted` output asks whether the composite lies in `P_eta`
(Definition 2.5). These predicates need not agree.

| History | Per-switch P_eta membership | J | Composite admitted | Period at each window |
|---|---|---|---|---|
| B A A | true, true, true | true | true | 1, 1, 1, 1 |
| B C C | true, false, false | false | true | 1, 1, 0, 1 |
| B B A | true, true, true | true | true | 1, 1, 1, 1 |
| B B C | true, true, false | false | false | 1, 1, 1, 1 |

Every row has cumulative costs `(1/3, 2/3, 1, 4/3)`.
The three observations used by `poa_stitch.py` are defined exactly as follows:

| Output name | Information retained |
|---|---|
| `final_cycle_cost` | Final transported cycle, as sorted nonzero edge-coefficient pairs, and the full cumulative-cost trace |
| `period_trace_cost` | Full four-window period trace and full cumulative-cost trace |
| `period_cost_membership` | The preceding period-and-cost view plus the three per-switch P_eta membership bits |

B A A and B C C have the same actual composite graph map B, hence the same final
transported cycle, and also have the same costs. Their `final_cycle_cost`
observations coincide while `J` differs. B B A and B B C have the same entire
period-and-cost trace while `J` differs. Each pair lies in a mixed fibre of
its declared observation, so neither reduced observation determines `J` on
`H`, by PoA Theorem 3.1.

For every attained fibre the imported `fibre_decision` returns `admit` when
all target values are true, `reject` when all are false, and
`insufficient observation` when both occur (Corollary 3.4).
The imported `factors_through` checks constancy on all attained fibres.
A request for an unattained observation raises an error; an empty fibre is not
admitted by vacuity.

The membership-enriched observation determines `J` by conjunction of its
bits, so factorisation holds by construction. This demonstrates informational
sufficiency of that record for this target; it is not an independent proof that
membership was computed correctly, that the bits are available to a real
observer, or that the witness captures physical identity.

The two generic PoA functions receive event words as history identifiers and
callbacks for these observations and this target. This bridge does not use the
integer-defect `Seam` representation, the defect-cocycle results or the entropy
routines. Event names, intermediate cycles and other diagnostics remain in the
full JSON output but are excluded from the two reduced observations. The
counterexamples establish indistinguishability only under those projections,
not under the full output or an unspecified larger history class.

## Boundary recomposition with ordered windows

`recomposition_stitch.py` loads XIV, XV, Identity and PoA through the PoA
adapter, then constructs an accounting path with four windows of cost `1/3`
and capacity `2`. Its states, full edge set and costs come from the actual
converted XIV substrate. Each original edge carries one declared unit span.

The endpoint predicate asks for a route from `0` to `4`, of declared span at
most `4`, with total burden strictly below `2`. A cut removes the interior state
of the chain `1 -> 2 -> 3` and refuses undeclared contacts. A fold replaces that
chain by one macro-edge retaining its complete ordered window trace, total
burden and declared span. A donor uses typed entry/exit ports and a complete,
injective map with fresh internal states.

| Construction | Complete endpoint route | Burden | Declared span | Requested route IE |
|---|---|---|---|---|
| Original | `0,1,2,3,4` | `4/3` | `4` | `m_IE = 0`, 4 traversals |
| Cut | none | — | — | not requested |
| Fold | `0,1,3,4` | `4/3` | `4` | `m_IE = 0`, 3 traversals |
| Cheap donor | `0,1,5,3,4` | `1` | `4` | `m_IE = 0`, 4 traversals |
| Costly donor | `0,1,5,3,4` | `8/3` | `4` | `UPPER_SUBCRITICAL_REQUIRED` |

The original one-window/one-edge correspondence above applies before folding.
The folded edge has span `2` and retains two windows, while the lower IE
capacity counts traversals, giving `3` for the folded route. Neither count is
continuous physical time. `first_crossing` reports the end of the first
declared window whose cumulative burden reaches the capacity.

The costly donor has a complete route but fails the strict endpoint budget.
It still satisfies XV's global nestability predicate through a shorter route;
the full requested route's refusal is not global non-nestability. The report
keeps these two answers separate.

A shape observation retains topology, endpoints, horizon and capacity but hides
weights, spans and window traces. The cheap and costly donors have the same
shape and opposite endpoint verdicts. PoA therefore returns `insufficient
observation` on that attained fibre; full-graph observations return `admit` and
`reject` respectively. Equal total cost and span also fail to determine first
crossing: windows `(1/3,2/3)` and their reversal cross `1/2` after different
windows. The final strict-budget predicate is nevertheless determined by the
total cost. These are two distinct targets.

The chain fold is an explicit finite construction. It preserves the accounting
trace on that chain; arbitrary graphs, arbitrary gluing, shared-control
viability and identity of the recomposed carrier are outside this example.
The original Identity certificate is replayed during loading, but
`identity_for_new_graph` remains `not_established`. The construction relates to
[Severance Defect and the Binding Functional](https://doi.org/10.17605/OSF.IO/5VJMR),
whose coupled-assembly result requires additional conditions. The distinction
between an aggregate and an ordered trajectory is also discussed in
[The Thousand-Year Warrior II, or The Person Is Not a Sum](https://doi.org/10.17605/OSF.IO/MJPDX);
that essay is not a physical-duration theorem.

## Finite Severance catalogue

`severance_stitch.py` implements a scoped finite instance of
[Severance Defect and the Binding Functional](https://doi.org/10.17605/OSF.IO/5VJMR),
Definitions 2.2, 3.1 and 3.3 and Proposition 3.4. It imports the same checked
Identity and PoA sources; the source verifier remains a separate toy certificate.
The adapter constructs canonical presentations with fields `states`, `edges`,
`admissible`, `phi` and `capacity`. Its `phi` table retains exact costs for the
supplied admitted paths; it does not retain the substrate's entire Phi function.

Operational comparison is declared only for the canonical complete
`Presentation` catalogue constructed by `fixture`, separately for each audit.
Two represented presentations are equivalent iff a bijection of states
preserves directed edges, the supplied admissible paths, every exact cost in
the supplied phi table, capacity C, and the marked source and endpoint for P.
The full-path criterion marks 0 -> 4; the separate prefix criterion marks
0 -> 2. The phi table contains costs of supplied admitted paths, not the
substrate's entire Phi function. In this catalogue all non-capacity fields
have the same canonical representation and C is 1, 2 or 3. Equal C selects
the same represented presentation; different C precludes equivalence, so
C comparison decides equivalence on each declared catalogue. Tuple equality
is used on these canonical values; reordered or relabelled variants are not
additional inputs. q, e, P, entropy and reconstruction concern only this
fixed catalogue and its declared model deletions. No canonical quotient of
arbitrary substrates or whole NC systems, physical deletion or physical
reconstruction is established.

The capacity classes are C1/C2 and C2/C3 on the same accounting path, with
four supplied window costs of 1/3. Capacity hiding removes C from the represented
observation; budget-decision availability asks whether all compatible completions
have the same strict-budget answer. It does not mean that answer is positive.
Directed-edge deletion changes the represented edge set and filters admitted
paths and their stored costs. The separate reachability criteria retain their
marked source and endpoint. These are deletions in a finite model.

The functional defect concerns P(e(S)); the PoA observation decision concerns
P on original complete presentations. Point posterior entropy and its prior-
weighted mean are distinct outputs. Reconstruction is an inverse on the entire
declared finite catalogue when every observation fibre is a singleton; it does
not reconstruct an unknown graph or execute a physical repair. Selected Identity
witness preservation remains a separate output, not a whole-system identity claim.

## Person budgets on selected ordered routes

`person_stitch.py` loads the pinned `person_harness.py` through the same verified
source-buffer loader used by the existing connections. `person_adapter.py`
requires a complete selected route from the recomposition graph, flattens its
edge traces in route order and constructs one `Person.Window(cost, span)` per
existing window. Costs remain exact nonnegative rational numbers; spans remain
the supplied positive integers. A folded edge retains its constituent windows.
These spans are declared coordinates, not measured physical durations.

The capacity is the graph's exact positive rational capacity. For each window,
the prefix report retains `(capacity - cumulative cost, cumulative span)`,
including the final prefix. Final survival means that the final budget is
strictly positive; whole survival means every prefix budget is strictly
positive. The first crossing is the first budget at or below zero, reported as
`(one-based window index, cumulative span)`.

At capacity `2`, the existing cases give:

| Case | Ordered costs | Final budget | Final survival | Whole survival | First crossing |
|---|---|---|---|---|---|
| Original | `1/3, 1/3, 1/3, 1/3` | `2/3` | true | true | none |
| Fold | `1/3, 1/3, 1/3, 1/3` | `2/3` | true | true | none |
| Cheap replacement | `1/3, 1/6, 1/6, 1/3` | `1` | true | true | none |
| Costly replacement | `1/3, 1, 1, 1/3` | `-2/3` | false | false | `(3, 3)` |

The costly case's complete prefix list is `(5/3, 1), (2/3, 2), (-1/3, 3),
(-2/3, 4)`. The costly graph itself is not functional. The `branched` graph adds
a cheap sibling edge `0 -> 4` of cost `1/4`, making that graph functional while
the selected costly route still crosses the budget boundary and fails whole
survival. That sibling does not change the costly route's verdict. The cut
has no complete route and therefore no
Person trace; the adapter does not substitute an empty trace.

Nonnegative costs make prefix budgets nonincreasing. At fixed capacity, the
final budget is their minimum, so final and whole survival are equivalent in
this class. They remain separately named outputs. Order can change the first
crossing, while positive integer spans change its coordinate: doubling the
costly case's declared spans gives `(3, 6)` with the same survival verdict.
Comparison uses the same capacity for both routes and delegates to Person's
`loss_status`, which requires an admissible surviving baseline. This finite
connection does not establish moral status, physical duration or whole-system
identity.

## Execution and evidence

`python -B tectonica.py` first validates all five dependency gitlinks against
HEAD and their clean checkouts, then runs six children: `pinned_sources.py`
executes the existing XIV/XV construction and its controls, followed by
`identity_stitch.py`, `poa_stitch.py`, `recomposition_stitch.py`,
`severance_stitch.py --teeth` and `person_stitch.py`. The fourth child executes its 16 checks before
printing its report; the fifth runs eleven finite Severance checks; the sixth
runs eight Person connection checks before reporting selected-route budgets.
These children also refuse when the number of checks actually executed differs
from the declared count. A standalone `python -B severance_stitch.py` prints the
finite profiles.
The first failed child stops the launch and its nonzero status is returned.
`--check-only` checks dependency pins, cleanliness and required entry files;
it does not run certificate replay or the mathematical checks. Each standalone
adapter also checks all pins before importing layer code.

The Identity adapter reports the loaded source and certificate hashes, cycle and
period traces, cumulative costs, accounting-prefix burdens, final pairing verdict,
period constancy, global-class diagnostic and IE result. The PoA adapter adds its
source hash, the 27 histories' per-switch and composite preservation readouts,
and the three fibre audits. The root loader compares every consumed dependency
source and certificate buffer with its blob at the captured commit, then
executes or parses that same buffer. It accepts exact bytes or whole LF-to-CRLF
conversion of LF text. A later content change is refused on the next read; it
cannot change a buffer already read and checked. Hashes identify the consumed
bytes and are not scientific certification. Only modules recorded by this
loader may be reused; foreign cached modules are refused.

The root package, Python, Git and their runtime environment remain trusted. Git
reads discard inherited `GIT_*` overrides and disable replacement objects. They
require Git support for `--no-lazy-fetch`; unsupported versions and missing
promised objects are refused without retrieval. These checks bind dependency
inputs to selected commits; they do not provide process
isolation against an actor controlling the trusted runtime.

`python -B -m unittest -v test_tectonica test_pinned_sources test_identity_stitch test_poa_stitch test_recomposition_stitch test_person_stitch`
runs launch fixtures, temporary Git source-binding fixtures and checks with
the actual pinned dependencies. Source-binding checks cover changed buffers,
captured commits, line endings, module reuse, failed imports and refusal of a
missing promised blob without fetching from a local promisor. The Identity
checks include corruptions of cycle transport, composition, period traces,
survival flags, verdict labels and accounting prefixes, plus a cancelling-path
positive control. PoA checks include both covector basis coordinates, rejection
of an incomplete graph map, path-backtracking invariance, literal counterexample
values, the exact projections and all three fibre decisions. The recomposition
tests check the boundary adapter's source-edge, source-vertex, cost and capacity
contracts on substituted carriers; the pinned carrier itself is read by the
launcher's fourth child. These tests are
distinct from the upstream repositories' own complete suites. Longer user
schedules can make the imported finite IE enumeration expensive; the default
examples are deliberately small. No arbitrary schedule-input CLI is provided.

`python -B break_recomposition_stitch.py` runs 34 copied model mutations and
controls against the finite recomposition adapter, once normally and once with
`-O`. Each negative case requires its expected first named failure. The
literal-assignment reordering control must preserve all checks, the reach
control must reach the changed line, and deleting one named check must be
refused by the executed-count check. Mutation anchors are tied to this adapter
version. These cases test the finite model and its refusals, not a general
composition theorem or a new Identity witness.

`python -B break_severance_stitch.py` runs 14 copied model mutations and
controls against the finite Severance adapter, normally and with `-O`. Eleven
cases require their expected first named failure; the reordering control must
preserve all checks, the start-vertex control must reach the edge-loss check,
and deleting one named check must be refused by the executed-count check. These
cases test the declared finite catalogue, not a general deletion theorem.

A negative Person survival verdict is a valid
scientific result, not an execution error. `test_person_stitch.py` checks the
real pinned source buffer, exactly one verified read, changed bytes, a foreign
module cache entry and refusal status. `break_person_stitch.py` makes twelve
in-memory adapter changes, requires each expected marker to fail first and
covers all eight connection checks; run it with `python -B` and separately with
`python -B -O`. The mutations preserve the pinned source files.


## Sources

- [Identity Does Not Drift](https://doi.org/10.17605/OSF.IO/4NMTW): published
  `harness/switch_transport.py`, `emergence_verify.py` and
  `emergence_certificate.json` at the recorded dependency commit.
- [ONTOΣ XV](https://doi.org/10.17605/OSF.IO/EAUD5): `graph_hodge.py`,
  `core_reduction.py`, `nestability.py`, `xiv_stitch.py` and repository errata.
- [ONTOΣ XIV](https://doi.org/10.17605/OSF.IO/KAGMH): finite-state harness,
  robustness companion and repository errata.
- [The Physics of Abstraction](https://doi.org/10.17605/OSF.IO/QJ5BR):
  Definitions 2.1–2.5, Theorem 3.1, Corollary 3.4 and `harness/seam_audit.py`.
  Section 10.1 gives the protected-covector connection; §10.5 separates
  persistence from viability. The physical correspondence obligations in §7.2
  and the informational-only boundary in §12.7 remain outside this composition.
- [Severance Defect and the Binding Functional](https://doi.org/10.17605/OSF.IO/5VJMR):
  Definitions 2.2, 3.1 and 3.3 and Proposition 3.4 in the finite catalogue; its
  own source verifier remains a separate toy certificate.
- [The Thousand-Year Warrior II, or The Person Is Not a Sum](https://doi.org/10.17605/OSF.IO/MJPDX):
  its pinned companion `person_harness.py` supplies finite prefix budgets,
  final and whole survival and the first crossing of an ordered window trace.
  The essay does not establish physical duration or moral status for these graphs.

The deposited scientific files and previous release tags are preserved.
