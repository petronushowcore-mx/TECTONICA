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

This release demonstrates an executable connection between two published NC2.5
layers: ONTOΣ XIV and XV. Further published layers are planned for later releases.
The connection combines XIV's finite substrate and Independent-Exhaustion machinery
with XV's nestability and graph-transport machinery.

## Scope and limits

The current construction takes a supplied finite, admissible, subcritical upper
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

## Layers

| Layer | Responsibility |
|---|---|
| [ONTOΣ XIV](https://github.com/petronushowcore-mx/NC2.5-ONTOSigma-XIV-Cross-Layer-Forgetful-Separation-corpus) | Finite substrates, admissibility, IE and robustness. |
| [ONTOΣ XV](https://github.com/petronushowcore-mx/NC2.5-ONTOSigma-XV-Spin-Channel-and-Nestability-corpus) | Nestability, graph cohomology and transport. |
| TECTONICA | Selects exact dependency commits and invokes their existing connection. |

The two `layers/` entries are Git submodules. Their committed gitlinks fix the
versions; `.gitmodules` gives their source URLs. Dependencies are not selected from
moving branch tips at launch. The adapter remains in XV; this repository does not
copy it. After initialising the submodules, read `layers/XV/INTEGRATION.md`
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

A successful launch prints the selected commits and runs XV's existing
`xiv_stitch.py --xiv-root ... --teeth`. The child reports the loaded source hashes,
construction scenarios and separate transport results. Its exit status is preserved;
a failed dependency check returns 2 before starting the child. Commit pins identify
Git content; checkout conversions and the Python version are separate reproducibility
inputs. No guarantee is made against another process changing files during a run.

Local launch-contract tests use explicit Git-response fixtures and require no
initialised submodules:

```text
python -B -m unittest -v test_tectonica
python -B -O -m unittest -v test_tectonica
```

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
These identify the source works, not a separate DOI for TECTONICA.

Copyright (c) 2026 Maksim Barziankou (MxBv), The Urgrund Laboratory.
[CC BY-NC-ND 4.0](LICENSE). Contact: research@petronus.eu.
