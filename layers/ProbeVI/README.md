# Individual Viability Does Not Compose

NC2.5 Empirical Probes — Part VI.

Maksim Barziankou (MxBv), The Urgrund Laboratheory.

Companion to [Individual Viability Does Not Compose](https://doi.org/10.17605/OSF.IO/WFBX6).
Axiomatic Core cited by the paper: [NC2.5 v2.1](https://doi.org/10.17605/OSF.IO/NHTC5).

This code checks a three-state, one-input linear counterexample to the composition
of individual admissible sets. It uses exact rational arithmetic and requires
Python 3.10 or newer with only the standard library. No network connection or
account is required.

This MIT companion is included in TECTONICA at `layers/ProbeVI` and is
bound to the TECTONICA root commit. From that directory:

```text
cd harness
python -B probe_vi.py
python -B -m unittest discover -p "test_*.py" -v
```

The certificate command emits deterministic JSON with six named checks.
The test suite contains seven tests, including targeted model mutations,
shared-control examples, set-helper regressions and third-coordinate dynamics
checks. `certificate.json` records the unmodified certificate and is compared
with the computed result by one test.

The canonical model has drift matrix rows `(0,0,1)`, `(0,0,1)`, `(0,0,0)`, input
vector `(1,-1,0)`, coordinate constraint rows `(1,0,0)`, `(0,1,0)`, initial state
`(0,0,1)`, zero constraint offsets and control interval `[-1,1]`. Each individual
constraint has a constant admissible control, while the canonical joint problem
has no common admissible control preserving both constraints for every `t >= 0`.

`check_sum_rate(model)` alone computes a local coordinate-sum rate. A positive
rate with a zero control coefficient is not, for arbitrary constraint rows,
a joint-viability verdict. The canonical common-control conclusion also requires
`check_set_separation(model)`: canonical constraints, both constrained drifts
equal to the third coordinate, input gains `+1` and `-1`, a constant third
coordinate and the exact-set identities. The individual trajectory certificates
must also hold.

The companion checks this explicitly specified counterexample, tangency and
boundary hulls, and the supplied negative controls. It is not a general viability
solver and does not reproduce the examined paper's numerical examples or complete
sampling implementation. The paper states the mathematical proof and its limits.
A local code copy does not establish acceptance or publication status of the paper.

Code and this documentation are licensed under the MIT License; see LICENSE.
The paper has its separate CC BY-NC-ND 4.0 licence and is not included here.

## Acknowledgements

The idea for this common-control integration emerged while checking *Probe VI — Individual Viability Does Not Compose: A Common-Control Counterexample*, prompted by [*Polytopic Inner Approximation of Admissible Sets for Linear Systems* (arXiv:2607.29664v2)](https://arxiv.org/html/2607.29664v2) by Jean Lévine, Philipp Rumschinski, Franz Rußwurm, and Stefan Streif. I am sincerely and wholeheartedly grateful to its authors for the insight their work inspired.
