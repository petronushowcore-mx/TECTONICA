<p align="center">
  <img src="assets/layers.gif" alt="Animated XIV/XV construction with a moving violet identity witness and a green Physics of Abstraction observation channel, with future publication layers above." width="1200">
</p>

<p align="center">
  <strong>Independently evolving layers. Explicit, executable connections.</strong><br>
  <a href="#scope-and-limits">Scope</a> ·
  <a href="#layers">Layers</a> ·
  <a href="#run">Run</a> ·
  <a href="#versioning-and-additional-layers">Extend</a> ·
  <a href="assets/layers.png">Static diagram</a>
</p>

This composition connects four published NC2.5 layers: ONTOΣ XIV, ONTOΣ XV,
Identity Does Not Drift and The Physics of Abstraction. It combines finite
Independent Exhaustion, graph transport, channel-switch histories and a check
of what selected observations can determine. Further publication layers can
be added through explicit connections.

The animation illustrates the XIV/XV construction with Identity's witness
transport shown as a moving violet marker across the two planes. Physics of
Abstraction appears as a green observation channel beside the construction:
different histories can share one readout. The moving markers are schematic.

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

Physics of Abstraction adds an observation audit over all 27 three-switch words
in the certificate's A/B/C alphabet. Its target is preservation of the full fixed
covector at every switch, distinguished from preservation by the composite map.
A final-cycle-and-cost view and a period-trace-and-cost view each hide conflicting
target values. Adding the per-switch membership bits determines this target by
construction; that factorisation is not an independent validation of the bits.

These conclusions concern the declared finite catalogue and projections.
The full output contains more information than those reduced views. No physical
identity criterion or isolation boundary between an acting process and an
observer is established. Read [the four-layer connection](INTEGRATION.md) for
the types, counterexamples and exact observation definitions.

## Layers

| Layer | Responsibility |
|---|---|
| [ONTOΣ XIV](https://github.com/petronushowcore-mx/NC2.5-ONTOSigma-XIV-Cross-Layer-Forgetful-Separation-corpus) | Finite substrates, admissibility, IE and robustness. |
| [ONTOΣ XV](https://github.com/petronushowcore-mx/NC2.5-ONTOSigma-XV-Spin-Channel-and-Nestability-corpus) | Nestability, graph cohomology and transport. |
| [Identity Does Not Drift](https://github.com/petronushowcore-mx/Identity-Does-Not-Drift) | Channel schedules, exact witness transport and an independently replayed finite certificate. |
| [The Physics of Abstraction](https://github.com/petronushowcore-mx/physics-of-abstraction) | Factorisation through observations and three-valued decisions on attained observation fibres. |
| TECTONICA | Selects exact dependency commits, checks the schedule-to-substrate correspondence and audits declared observations of finite switch histories. |

The four `layers/` entries are Git submodules. Their committed gitlinks fix the
versions; `.gitmodules` gives their source URLs. Dependencies are not selected from
moving branch tips at launch. The original IE adapter remains in XV. This
repository's `identity_stitch.py` implements the schedule composition;
`poa_stitch.py` adds the finite observation audit. Both import the pinned layer
code. After initialising the submodules, read `layers/XV/INTEGRATION.md` for the
construction and its premises, and `layers/XIV/ERRATA.md` and
`layers/XV/ERRATA.md` for the corrections at those recorded versions.
The deposited scientific source files and earlier repository history are preserved.

## Run

Python 3 and Git with support for `--no-lazy-fetch` are required. Git versions
that do not recognise this option are refused. Python dependencies are
standard-library only.
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
Missing promised objects are refused without retrieval.
Run only trusted checkouts: their Python code is executed.

A successful launch prints all four selected commits and runs three children in
order: `pinned_sources.py` runs XV's construction and controls, followed by
`identity_stitch.py` and
`poa_stitch.py`. The first failed child stops the sequence and its exit status
is returned. Dependency checks fail with status 2 before any child starts.

The results include source hashes, the four original schedule traces,
prefix-by-prefix cost correspondence, separate transport diagnostics and a
boundary IE witness for each schedule. The PoA child adds all 27 three-switch
histories and three observation audits, each reporting its fibres and whether
the target factors through that observation. Successful execution does not mean
every history is admitted: a mixed fibre is reported as `insufficient observation`.

Before executing a dependency module or parsing the Identity certificate,
`pinned_sources.py` compares the bytes read with the blob at the selected commit.
It executes or parses that same buffer. Exact bytes and whole LF-to-CRLF
conversion of LF text are accepted; other content changes are refused. Reported
hashes identify the consumed bytes, including their line endings. The loader
reuses only its own recorded modules and refuses foreign cached modules.

The root package, Python, Git and their runtime environment must be trusted.
Git commands ignore inherited `GIT_*` overrides and replacement objects. This
binds consumed dependency content to the selected commits; it does not isolate
the process from an actor who can alter the trusted runtime. The Python version
and accepted checkout line endings remain separate reproducibility inputs.

Local launch-contract tests use explicit Git-response fixtures and require no
initialised submodules:

```text
python -B -m unittest -v test_tectonica
python -B -O -m unittest -v test_tectonica
```

Integration tests require the four initialised, clean dependencies:

```text
python -B -m unittest -v test_tectonica test_pinned_sources test_identity_stitch test_poa_stitch
python -B -O -m unittest -v test_tectonica test_pinned_sources test_identity_stitch test_poa_stitch
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
The Physics of Abstraction: [10.17605/OSF.IO/QJ5BR](https://doi.org/10.17605/OSF.IO/QJ5BR).
These identify the source works, not a separate DOI for TECTONICA.

Copyright (c) 2026 Maksim Barziankou (MxBv), The Urgrund Laboratory.
[CC BY-NC-ND 4.0](LICENSE). Contact: research@petronus.eu.
