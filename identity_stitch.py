"""Compose the pinned Identity schedule with XV transport and XIV finite IE.

This is an exact finite example on Identity's certified two-loop carrier.
Window costs define a separate directed accounting path; they are supplied
model inputs, not a cost law derived from the topological maps.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import tectonica
import pinned_sources


class Refusal(Exception):
    pass


def require(condition, marker):
    if not condition:
        raise Refusal(marker)


def load_sources(root):
    """Check all dependency pins before executing any dependency module."""
    selected = tectonica.checked_layers(root)
    xiv, xv, identity_root = [selected[name][0] for name in ('XIV', 'XV', 'Identity')]
    path = xv / 'harness/xiv_stitch.py'
    stitch = pinned_sources.load_xiv_stitch(selected)
    api = stitch.load_sources(xiv, xv)
    identity = stitch._load('tectonica_identity_transport', identity_root / 'harness/switch_transport.py')
    replay = stitch._load('tectonica_identity_replay', identity_root / 'harness/emergence_verify.py')
    provenance = dict(api.provenance)
    provenance['xiv_stitch'] = {'path': str(path), 'sha256': stitch._xiv_stitch_source_sha256}
    for name, module in [('identity_transport', identity), ('identity_replay', replay)]:
        provenance[name] = {'path': module.__file__, 'sha256': module._xiv_stitch_source_sha256}
    certificate_path = identity_root / 'harness/emergence_certificate.json'
    certificate_bytes = pinned_sources.read_pinned(selected, certificate_path)
    certificate = json.loads(certificate_bytes.decode('utf-8'))
    verify_certificate(replay, certificate)
    provenance['identity_certificate'] = {'path': str(certificate_path),
        'sha256': hashlib.sha256(certificate_bytes).hexdigest()}
    return SimpleNamespace(stitch=stitch, api=api, identity=identity, replay=replay,
        certificate=certificate, provenance=provenance,
        commits={name: revision for name, (_, revision) in selected.items()})


def verify_certificate(replay, certificate):
    """Require the independent bounded-model replay before interpreting its data."""
    try:
        replay.verify_certificate(certificate)
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        raise Refusal('CERTIFICATE_REJECTED: ' + str(exc)) from exc


def certified_model(data):
    """Interpret only a certificate accepted by Identity's independent verifier."""
    cert = data.certificate
    verify_certificate(data.replay, cert)
    basis = {name: i for i, name in enumerate(cert['model']['homology_basis'])}
    events = cert['protected_channel']['generators'] + [cert['critical_extension']['event']]
    maps = {event['name']: {basis[edge]: [(basis[step[0]], {'+': 1, '-': -1}[step[1]])
             for step in path] for edge, path in event['images'].items()} for event in events}
    eta = {i: F(c) for i, c in enumerate(cert['protected_channel']['primitive_common_fixed_covector'])}
    gamma = {i: c for i, c in enumerate(cert['order_effect']['initial_cycle'])}
    return maps, eta, gamma


def compose(first, second):
    """Apply first, then second, retaining path order and reversal signs."""
    out = {}
    for edge, path in first.items():
        image = []
        for target, sign in path:
            subpath = second[target]
            image.extend(subpath if sign == 1 else [(e, -s) for e, s in reversed(subpath)])
        out[edge] = image
    return out


def chain(cycle):
    return {edge: value for edge, value in cycle.items() if value != 0}


def accounting_substrate(data, windows, capacity):
    """One supplied schedule window becomes one edge of a distinct directed path."""
    require(isinstance(capacity, (int, F)) and not isinstance(capacity, bool) and capacity > 0,
            'FINITE_POSITIVE_EXACT_CAPACITY')
    costs = [sum((F(increments.get(channel, F(0))) for channel in active), F(0))
             for active, increments in windows]
    states = list(range(len(windows) + 1))
    edges = list(zip(states, states[1:]))
    source = data.api.nest.Sub(states, edges, dict(enumerate(costs)), C=capacity)
    return data.stitch.to_xiv_sub(source, data.api), tuple(states)


def connect(data, event_names, windows, n_channels, concurrent_limit, capacity):
    """Check one finite schedule and its explicit per-window accounting relation.

    The cycle carrier is the certified bouquet, not the accounting path.
    Longer schedules can make the imported finite IE enumeration expensive.
    """
    require(len(windows) == len(event_names) + 1, 'WINDOW_SWITCH_COUNT')
    maps, eta, gamma = certified_model(data)
    require(all(name in maps for name in event_names), 'UNKNOWN_EVENT')
    vertices, edges = ['v'], [('v', 'v'), ('v', 'v')]
    carrier = data.identity.Carrier(vertices, edges)
    graph = data.api.graph.Graph(vertices, edges)
    vmap = {'v': 'v'}
    schedule = data.identity.Schedule(carrier, n_channels=n_channels, k=concurrent_limit)
    for j, (active, increments) in enumerate(windows):
        schedule.add_window(active, increments)
        if j < len(event_names):
            schedule.add_switch(vmap, maps[event_names[j]])
    # Schedule validates exact nonnegative costs and full declared-channel coverage.
    periods, budgets = schedule.run(eta, gamma, require_full_coverage=True)
    z_identity, z_xv = dict(gamma), dict(gamma)
    composite = data.identity.identity_emap(carrier)
    cycles = [chain(z_xv)]
    xv_periods = [data.api.graph.period(eta, z_xv)]
    for name in event_names:
        event = maps[name]
        graph.check_graph_map(graph, vmap, event)
        z_identity = data.identity.pushforward(carrier, event, z_identity)
        z_xv = data.api.graph.induced_pushforward(event, z_xv)
        require(chain(z_identity) == chain(z_xv), 'CYCLE_TRANSPORT_AGREEMENT')
        composite = compose(composite, event)
        graph.check_graph_map(graph, vmap, composite)
        composed = data.api.graph.induced_pushforward(composite, gamma)
        require(chain(composed) == chain(z_xv), 'COMPOSED_TRANSPORT_AGREEMENT')
        cycles.append(chain(z_xv))
        xv_periods.append(data.api.graph.period(eta, z_xv))
    require(periods == xv_periods, 'PERIOD_TRACE_AGREEMENT')
    verdict, survived = data.api.core.transport_classify(
        graph, graph, vmap, composite, [gamma], eta, eta)
    require(survived == [periods[-1] != 0], 'PAIRING_SURVIVAL_AGREEMENT')
    expected_verdict = 'PRESERVING' if periods[-1] != 0 else 'ANNIHILATING'
    require(verdict == expected_verdict, 'TRANSPORT_VERDICT_AGREEMENT')
    upper, trajectory = accounting_substrate(data, schedule.windows, capacity)
    prefix_burdens = [upper.Phi(trajectory[:j + 2]) for j in range(len(windows))]
    require(prefix_burdens == budgets, 'WINDOW_ACCOUNTING_AGREEMENT')
    lower, nu = data.stitch.construct_lower(upper, trajectory, data.api)
    ie = data.stitch.verify_constructed_ie(upper, lower, nu, trajectory, data.api)
    return {'events': list(event_names), 'cycles': cycles,
        'periods': [str(value) for value in periods],
        'cumulative_costs': [str(value) for value in budgets],
        'accounting_prefix_burdens': [str(value) for value in prefix_burdens],
        'pairing_verdict': verdict, 'pairing_survived': survived[0],
        'period_constant': all(value == periods[0] for value in periods),
        'global_class_zero': data.stitch.global_class_zero(graph, eta, data.api),
        'ie': ie, 'full_regime_w': 'NOT_EVALUATED'}


EXAMPLES = (
    ('ABAB', ['1', '1', '1', '1', '1']),
    ('BC', ['1', '1', '0']),
    ('CB', ['1', '-1', '-1']),
    ('BCC', ['1', '1', '0', '1']),
)


def examples(data):
    """Small literal traces from the declared model, each linked to its own IE path."""
    rows = []
    for word, expected in EXAMPLES:
        windows = [([j], {j: F(1, 3)}) for j in range(len(word) + 1)]
        row = connect(data, word, windows, len(windows), 1, F(2))
        require(row['periods'] == expected, 'EXAMPLE_PERIODS_' + word)
        require(row['global_class_zero'] is False, 'EXAMPLE_NONZERO_GLOBAL_CLASS_' + word)
        rows.append(row)
    require(rows[1]['cumulative_costs'] == rows[2]['cumulative_costs'], 'ORDER_EXAMPLE_EQUAL_COSTS')
    return rows


def main():
    try:
        data = load_sources(Path(__file__).resolve().parent)
        rows = examples(data)
        print(json.dumps({'scope': 'finite certified-carrier schedules with explicitly assigned window costs',
            'commits': data.commits, 'source_provenance': data.provenance, 'cases': rows}, indent=2))
        print('IDENTITY_CONNECTION: PASS (4 finite schedules; window accounting and boundary IE)')
        return 0
    except (Refusal, tectonica.Refusal, OSError, ValueError) as exc:
        print('IDENTITY_CONNECTION: REFUSED ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
