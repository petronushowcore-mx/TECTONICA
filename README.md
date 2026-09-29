<p align="center">
  <img src="assets/layers.gif" alt="Animated illustrative connection between ONTOΣ XIV and XV, with further publication layers shown as future additions." width="1200">
</p>

<p align="center">
  <strong>Independently evolving layers. Explicit, executable connections.</strong><br>
  <a href="#scope-and-limits">Scope</a> ·
  <a href="#layers">Layers</a> ·
  <a href="#run">Run</a> ·
  <a href="#versioning-and-additional-layers">Extend</a> ·
  <a href="assets/layers.png">Static diagram</a>
</p>

This composition connects three published NC2.5 layers: ONTOΣ XIV, ONTOΣ XV and
Identity Does Not Drift. It combines finite Independent Exhaustion, graph
transport and the history of channel switching. Further publication layers can
be added through explicit connections.

The animation above illustrates the original XIV/XV connection. The Identity
connection is specified and exercised below; it is not depicted in that image.

## Scope and limits

The XIV/XV construction takes a supplied finite, admissible, subcritical upper
trajectory with at least one transition. It constructs a lower substrate with
unit edge burdens, capacity equal to the traversal count, and explicit window
admissibility. XIV evaluates the resulting witness: `NESTED-BOUNDARY`, with
`m_IE = 0`. Finite positive capacity and no parallel directed edges are required;
self-loops and repeated traversals are allowed.

This establishes a formal IE witness, without positive-margin robustness,
physical hostability or epistemic independence. Transported pairing annihilation,
global class zero and full Regime W are distinct results. The full Regime W
conditions are not evaluated. The XV Bridge Law remains declared; physical
experiments and a general proof of XIV.2 are outside this executable connection.

Identity adds a certificate-defined two-loop carrier and exact schedule traces.
Its window costs are explicitly assigned to a separate directed accounting path,
then compared against XIV burdens at every prefix. The global cohomology class,
transported pairing, period constancy and IE verdict remain separate outputs.
Read [the three-layer connection](INTEGRATION.md) for the mapping and examples.

## Layers

| Layer | Responsibility |
|---|---|
| [ONTOΣ XIV](https://github.com/petronushowcore-mx/NC2.5-ONTOSigma-XIV-Cross-Layer-Forgetful-Separation-corpus) | Finite substrates, admissibility, IE and robustness. |
| [ONTOΣ XV](https://github.com/petronushowcore-mx/NC2.5-ONTOSigma-XV-Spin-Channel-and-Nestability-corpus) | Nestability, graph cohomology and transport. |
| [Identity Does Not Drift](https://github.com/petronushowcore-mx/Identity-Does-Not-Drift) | Channel schedules, exact witness transport and an independently replayed finite certificate. |
| TECTONICA | Selects exact dependency commits, runs the XIV/XV connection and checks the schedule-to-substrate correspondence. |

The three `layers/` entries are Git submodules. Their committed gitlinks fix the
versions; `.gitmodules` gives their source URLs. Dependencies are not selected from
moving branch tips at launch. The original IE adapter remains in XV. The schedule composition is implemented
in this repository's `identity_stitch.py` and imports the pinned layer code. After initialising the submodules, read `layers/XV/INTEGRATION.md`
for the construction and its premises, and `layers/XIV/ERRATA.md` and
`layers/XV/ERRATA.md` for the corrections at those recorded versions.
The deposited scientific source files and earlier repository history are preserved.

## Run

Python 3 and Git are required. Python dependencies are standard-library only.
Clone this repository and initialise its recorded dependencies:

```text
git clone https://github.com/petronushowcore-mx/TECTONICA.git
cd TECTONICA
git submodule update --init --recursive
python -B tectonica.py --check-only
python -B tectonica.py
python -B -O tectonica.py
```

The launcher requires each dependency to have the recorded commit and a clean
working tree, including untracked and ignored files. It refuses index flags that
hide working files. Use dedicated clean checkouts; keep results outside `layers/`.
Once the dependencies are present, the launcher does not fetch or update them.
Run only trusted checkouts: their Python code is executed.

A successful launch prints all three selected commits, runs XV's existing
`xiv_stitch.py --xiv-root ... --teeth`, then runs `identity_stitch.py`. The first
failed child stops the sequence and its exit status is returned. Dependency
checks fail with status 2 before any child starts. The results include source
hashes, four schedule traces, prefix-by-prefix cost correspondence, separate
transport diagnostics and a boundary IE witness for each schedule. Commit pins identify
Git content; checkout conversions and the Python version are separate reproducibility
inputs. No guarantee is made against another process changing files during a run.

Local launch-contract tests use explicit Git-response fixtures and require no
initialised submodules:

```text
python -B -m unittest -v test_tectonica
python -B -O -m unittest -v test_tectonica
```

Integration tests require the three initialised, clean dependencies:

```text
python -B -m unittest -v test_tectonica test_identity_stitch
python -B -O -m unittest -v test_tectonica test_identity_stitch
```

`--check-only` verifies dependency pins, cleanliness and required entry files;
it does not execute certificate replay or mathematical checks.

## Versioning and additional layers

Further layers from published NC2.5 works are planned. Each addition requires an
implemented connection and its compatibility checks before it joins a release.

Each release records one composition of independently versioned layers. Develop
changes to an existing layer in its own repository, then update its gitlink here
alongside the connection checks. A new layer brings its own declared inputs,
outputs and conditions of compatibility before joining the composition.

Publish a new release for a changed composition. Keep earlier release tags and
their recorded layer commits unchanged so that previous compositions can still
be checked out and reproduced.

## Sources and license

ONTOΣ XIV: [10.17605/OSF.IO/KAGMH](https://doi.org/10.17605/OSF.IO/KAGMH).
ONTOΣ XV: [10.17605/OSF.IO/EAUD5](https://doi.org/10.17605/OSF.IO/EAUD5).
Identity Does Not Drift: [10.17605/OSF.IO/4NMTW](https://doi.org/10.17605/OSF.IO/4NMTW).
These identify the source works, not a separate DOI for TECTONICA.

Copyright (c) 2026 Maksim Barziankou (MxBv), The Urgrund Laboratory.
[CC BY-NC-ND 4.0](LICENSE). Contact: research@petronus.eu.
