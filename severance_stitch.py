"""Static component excision on TECTONICA's actual finite accounting carrier.

Finite instance of Severance Defect and the Binding Functional, Definitions 2.2,
3.1, 3.3 and Proposition 3.4. Scientific links through PoA already exist.
This adapter models field and directed-edge excision, a separate functional
criterion and a finite static binding/reconstruction profile. It does not prove
arbitrary physical transfer, whole-system identity or infinite safety.

Operational comparison is declared only for the canonical complete
Presentation catalogue constructed by fixture, separately for each audit.
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
"""
from collections import defaultdict
from fractions import Fraction as F
from math import log2, isclose
from pathlib import Path
import argparse
import json
import sys
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent
START = 0
END = 4
EXPECTED_TEETH = 11


class Refusal(Exception):
    pass


def require(condition, marker):
    if not condition:
        raise Refusal(marker)


class Presentation(NamedTuple):
    states: tuple
    edges: tuple
    admissible: tuple
    phi: tuple
    capacity: object


def q_capacity(model):
    # Phi and Adm here are independent of C. No tau or verdict is retained.
    return model._replace(capacity=None)


def phi_gamma(model):
    return dict(model.phi)[tuple(range(END + 1))]


def budget_positive(model):
    require(model.capacity is not None, "CAPACITY_NOT_OBSERVED")
    return model.capacity - phi_gamma(model) > 0


def compatible(model, partial):
    return q_capacity(model) == q_capacity(partial) and (
        partial.capacity is None or model.capacity == partial.capacity)


def budget_decidable(omega, partial):
    completions = [model for model in omega if compatible(model, partial)]
    return bool(completions) and len({budget_positive(m) for m in completions}) == 1


def excise_edge(model, edge):
    edges = tuple(e for e in model.edges if e != edge)
    paths = tuple(path for path in model.admissible
                  if all(e in edges for e in zip(path, path[1:])))
    phi = tuple((path, value) for path, value in model.phi if path in paths)
    return model._replace(edges=edges, admissible=paths, phi=phi)


def reachable(model, endpoint=END):
    seen, pending = {START}, [START]
    while pending:
        vertex = pending.pop()
        if vertex == endpoint:
            return True
        for source, target in model.edges:
            if source == vertex and target not in seen:
                seen.add(target)
                pending.append(target)
    return False


def validate_audit(omega, weights, target, criterion):
    require(bool(omega) and len(set(omega)) == len(omega), "COMPARISON_CLASS")
    require(set(weights) == set(omega) and all(w > 0 for w in weights.values()),
            "FULL_SUPPORT_PRIOR")
    require(target in omega and criterion(target) is True, "NORMAL_BASELINE")


def entropy(fibre, weights):
    mass = sum((weights[m] for m in fibre), F(0))
    posterior = [float(weights[m] / mass) for m in fibre]
    return sum(-p * log2(p) for p in posterior if p > 0)


def audit(omega, weights, target, observation, excision, criterion, poa):
    """Return distinct functional, reconstruction and observation verdicts."""
    validate_audit(omega, weights, target, criterion)
    groups = defaultdict(list)
    for model in omega:
        groups[observation(model)].append(model)
    observed = observation(target)
    fibre = groups[observed]
    excised = excision(target)
    delta = 1 - int(criterion(excised))
    total = sum(weights.values(), F(0))
    mean = sum(float(sum((weights[m] for m in group), F(0)) / total)
               * entropy(group, weights) for group in groups.values())
    # This observational query concerns original complete presentations, not e(S).
    original_answer = poa.fibre_decision(
        omega, observation, criterion, observed).value
    return {
        "delta": delta,
        "binding_bits_at_target": entropy(fibre, weights),
        "mean_binding_bits": mean,
        "fibre_capacities": [str(m.capacity) for m in fibre],
        "posterior": [str(weights[m] / sum((weights[x] for x in fibre), F(0))) for m in fibre],
        "functional_before": criterion(target),
        "functional_after_excision": criterion(excised),
        "original_function_observation": original_answer,
        "uniform_reconstruction": all(len(group) == 1 for group in groups.values()),
    }


def reconstruct(omega, observation, observed):
    groups = defaultdict(list)
    for model in omega:
        groups[observation(model)].append(model)
    require(all(len(group) == 1 for group in groups.values()), "NO_UNIFORM_RECONSTRUCTION")
    inverse = {view: group[0] for view, group in groups.items()}
    require(observed in inverse, "OUTSIDE_DECLARED_CLASS")
    return inverse[observed]


def transfer_budget_status(before, omega, observation, observed):
    # A normal starting point is required for any assertion of new loss.
    require(budget_positive(before), "NORMAL_BASELINE")
    fibre = [model for model in omega if observation(model) == observed]
    require(bool(fibre), "OUTSIDE_DECLARED_CLASS")
    answers = {budget_positive(model) for model in fibre}
    if len(answers) != 1:
        return "insufficient_information"
    return "preserved" if True in answers else "confirmed_budget_loss"


def fixture(root=ROOT):
    """Import checked pins; enumerate the actual XIV accounting presentations."""
    import identity_stitch as identity
    import poa_stitch as transport_observation
    base = identity.load_sources(root)
    poa_data = transport_observation.load_sources(root)
    windows = [([j], {j: F(1, 3)}) for j in range(4)]
    models, margins = {}, {}
    for capacity in (1, 2, 3):
        upper, trajectory = identity.accounting_substrate(base, windows, F(capacity))
        paths = tuple(sorted(path for path in upper.trajs(len(trajectory)) if upper.Adm(path)))
        model = Presentation(tuple(sorted(upper.X)), tuple(sorted(upper.E)), paths,
                             tuple((path, upper.Phi(path)) for path in paths), upper.C)
        require(trajectory in paths, "ACTUAL_TRAJECTORY_ADMITTED")
        models[capacity] = model
        margins[capacity] = upper.C - upper.Phi(trajectory)
    selected = transport_observation.history_record(poa_data, "AAA")
    require(selected["P_eta_uninterrupted"], "ACTUAL_IDENTITY_WITNESS")
    return {"models": models, "margins": margins, "poa": poa_data.poa,
            "commits": base.commits, "identity_history": selected}


def profiles(data):
    models, poa = data["models"], data["poa"]
    omega = (models[1], models[2])
    optional = (models[2], models[3])
    equal = lambda domain: {m: F(1, 2) for m in domain}
    capacity = lambda domain, weights=None: audit(
        domain, weights or equal(domain), models[2], q_capacity, q_capacity,
        lambda view: budget_decidable(domain, view), poa)
    required = lambda m: excise_edge(m, (1, 2))
    unused = lambda m: excise_edge(m, (3, 4))
    return {
        "capacity_decision_lost": capacity(omega),
        "ambiguous_but_budget_decidable": capacity(optional),
        "path_broken_but_reconstructible": audit(
            optional, equal(optional), models[2], required, required, reachable, poa),
        "prefix_survives_component_excision": audit(
            optional, equal(optional), models[2], unused, unused,
            lambda m: reachable(m, 2), poa),
        "unequal_prior": capacity(omega, {models[1]: F(1, 4), models[2]: F(3, 4)}),
    }


def teeth(data):
    models = data["models"]
    report = profiles(data)
    failed = []
    seen = []
    def check(name, condition):
        seen.append(name)
        print(("ok " if condition else "FAIL ") + name)
        if not condition:
            failed.append(name)

    boundary = models[2]._replace(capacity=F(4, 3))
    check("exact_budget_boundary",
          data["margins"][2] == F(2, 3) and data["margins"][1] == F(-1, 3)
          and budget_positive(models[2]) and not budget_positive(models[1])
          and not budget_positive(boundary))
    domain = (models[1], models[2])
    check("loss_distinct_from_unknown",
          transfer_budget_status(models[2], domain, lambda m: m, models[1]) == "confirmed_budget_loss"
          and transfer_budget_status(models[2], domain, q_capacity, q_capacity(models[1])) == "insufficient_information"
          and transfer_budget_status(models[2], domain, lambda m: m, models[2]) == "preserved")

    point = report["capacity_decision_lost"]
    check("capacity_excision_profile",
          point["delta"] == 1 and point["binding_bits_at_target"] == 1
          and point["functional_before"] and not point["functional_after_excision"])
    optional = report["ambiguous_but_budget_decidable"]
    check("ambiguity_without_function_loss",
          optional["delta"] == 0 and optional["binding_bits_at_target"] == 1)
    # A fully observed C1 presentation has one determinate, negative answer.
    check("determinate_negative_is_decidable",
          budget_decidable((models[1], models[2]), models[1]))

    edge = report["path_broken_but_reconstructible"]
    check("model_edge_loss_despite_observation_admit",
          edge["delta"] == 1 and edge["binding_bits_at_target"] == 0
          and edge["original_function_observation"] == "admit"
          and edge["uniform_reconstruction"])
    prefix = report["prefix_survives_component_excision"]
    check("honest_prefix_excision_preserved",
          prefix["delta"] == 0 and prefix["binding_bits_at_target"] == 0)
    weighted = report["unequal_prior"]
    check("posterior_uses_declared_prior",
          weighted["posterior"] == ["1/4", "3/4"]
          and isclose(weighted["binding_bits_at_target"], 0.8112781244591328, abs_tol=1e-12))

    edge_domain = (models[2], models[3])
    view = lambda m: excise_edge(m, (1, 2))
    check("reconstruction_on_whole_class",
          all(reconstruct(edge_domain, view, view(m)) == m for m in edge_domain)
          and reachable(reconstruct(edge_domain, view, view(models[2]))))

    prior_rejected = False
    try:
        audit(domain, {models[1]: F(0), models[2]: F(1)}, models[2],
              q_capacity, q_capacity, lambda m: budget_decidable(domain, m), data["poa"])
    except Refusal as exc:
        prior_rejected = str(exc) == "FULL_SUPPORT_PRIOR"
    check("zero_prior_refused", prior_rejected)

    # The prior-weighted mean is a separate output. Two fibres with different
    # entropies and unequal mass separate it from the target's point entropy,
    # from an unweighted average over fibres and from zero.
    three = (models[1], models[2], models[3])
    sign = audit(three, {m: F(1, 3) for m in three}, models[2], budget_positive,
                 lambda m: m, budget_positive, data["poa"])
    check("mean_binding_is_prior_weighted",
          sign["binding_bits_at_target"] == 1
          and isclose(sign["mean_binding_bits"], 2 / 3, abs_tol=1e-12))
    require(EXPECTED_TEETH == 11 and len(seen) == 11, "TEETH_COUNT")
    print("teeth: %d/11" % (11 - len(failed)))
    return not failed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teeth", action="store_true", help="run the eleven finite behaviour checks")
    args = parser.parse_args(argv)
    data = fixture()
    if args.teeth:
        return 0 if teeth(data) else 1
    models = data["models"]
    domain = (models[1], models[2])
    output = {
        "scope": "Static finite accounting-presentation audit; identity is a separate target.",
        "commits": data["commits"],
        "exact_margins": {str(k): str(v) for k, v in data["margins"].items()},
        "budget_observation_scenarios": {
            "C2_to_C1": transfer_budget_status(models[2], domain, lambda m: m, models[1]),
            "C_hidden": transfer_budget_status(models[2], domain, q_capacity, q_capacity(models[1])),
        },
        "selected_AAA_identity_witness_from_pinned_source": data["identity_history"]["P_eta_uninterrupted"],
        "profiles": profiles(data),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    import identity_stitch
    import tectonica
    try:
        sys.exit(main())
    except (Refusal, identity_stitch.Refusal, tectonica.Refusal) as exc:
        # Dependency refusals are reported like the adapter's own refusals.
        print("FAIL " + str(exc))
        sys.exit(1)