"""Finite boundary recomposition on TECTONICA's pinned accounting carrier.

The declared window trace is auxiliary data, not physical time in XIV Sub.
A constructed IE witness does not certify whole-system identity or autonomy.
"""
from collections import Counter
from fractions import Fraction as F
from unittest.mock import patch
from pathlib import Path
from typing import NamedTuple
import json
import sys

ZERO = 0
ONE = 1
EXPECTED_TEETH = 16


class Refusal(Exception):
    pass


def require(condition, marker):
    if not condition:
        raise Refusal(marker)


class Window(NamedTuple):
    cost: F
    span: int


class Edge(NamedTuple):
    source: int
    target: int
    cost: F
    span: int
    trace: tuple


class Graph(NamedTuple):
    vertices: tuple
    edges: tuple
    capacity: F
    start: int
    goal: int
    horizon: int


class Port(NamedTuple):
    vertex: int
    polarity: str
    payload: str


class Boundary(NamedTuple):
    outgoing: Port
    incoming: Port
    trace: tuple


class Part(NamedTuple):
    vertices: tuple
    edges: tuple
    entry: Port
    exit: Port


def validate(graph):
    require(bool(graph.vertices) and len(set(graph.vertices)) == len(graph.vertices),
            "VERTEX_SET")
    require(graph.start in graph.vertices and graph.goal in graph.vertices
            and graph.start != graph.goal, "ENDPOINTS")
    require(isinstance(graph.capacity, F) and graph.capacity > 0, "CAPACITY")
    require(type(graph.horizon) is int and graph.horizon > 0, "HORIZON")
    pairs = [(e.source, e.target) for e in graph.edges]
    require(len(set(pairs)) == len(pairs), "UNIQUE_EDGES")
    for e in graph.edges:
        require(e.source in graph.vertices and e.target in graph.vertices, "EDGE_ENDPOINT")
        require(isinstance(e.cost, F) and e.cost >= 0, "EXACT_NONNEGATIVE_COST")
        require(type(e.span) is int and e.span > 0, "POSITIVE_SPAN")
        require(bool(e.trace) and all(isinstance(w.cost, F) and w.cost >= 0
                and type(w.span) is int and w.span > 0 for w in e.trace)
                and sum((w.cost for w in e.trace), F(0)) == e.cost
                and sum(w.span for w in e.trace) == e.span, "TRACE_ACCOUNTING")
    return graph


def routes(graph):
    validate(graph)
    completed = []
    pending = [((graph.start,), F(ZERO), 0)]
    while pending:
        path, cost, span = pending.pop()
        if path[-1] == graph.goal:
            completed.append((path, cost, span))
            continue
        for edge in graph.edges:
            next_span = span + edge.span
            if edge.source == path[-1] and next_span <= graph.horizon:
                pending.append((path + (edge.target,), cost + edge.cost, next_span))
    return tuple(completed)


def functional(graph):
    return any(cost < graph.capacity for _, cost, _ in routes(graph))


def edges_of(graph, path):
    by_pair = {(e.source, e.target): e for e in graph.edges}
    require(len(path) >= 2 and all(pair in by_pair for pair in zip(path, path[1:])),
            "DECLARED_COMPONENT_PATH")
    return tuple(by_pair[pair] for pair in zip(path, path[1:]))


def cut(graph, path=(1, 2, 3)):
    validate(graph)
    selected = edges_of(graph, path)
    require(len(path) >= 3 and len(set(path)) == len(path), "INTERNAL_CHAIN")
    removed = set(path[1:-1])
    declared = {(e.source, e.target) for e in selected}
    incident = {(e.source, e.target) for e in graph.edges
                if e.source in removed or e.target in removed}
    require(incident == declared, "UNDECLARED_BOUNDARY_CONTACT")
    trace = tuple(w for e in selected for w in e.trace)
    fragment = graph._replace(
        vertices=tuple(v for v in graph.vertices if v not in removed),
        edges=tuple(e for e in graph.edges
                    if e.source not in removed and e.target not in removed))
    validate(fragment)
    return fragment, Boundary(Port(path[0], "out", "window"),
                              Port(path[-1], "in", "window"), trace)


def compatible(boundary, part=None):
    require(boundary.outgoing.polarity == "out" and boundary.incoming.polarity == "in"
            and boundary.outgoing.payload == boundary.incoming.payload, "BOUNDARY_PORTS")
    if part is not None:
        require(part.entry.polarity == "in" and part.exit.polarity == "out"
                and part.entry.payload == boundary.outgoing.payload
                and part.exit.payload == boundary.incoming.payload, "DONOR_PORTS")


def fold(fragment, boundary):
    compatible(boundary)
    trace = boundary.trace
    edge = Edge(boundary.outgoing.vertex, boundary.incoming.vertex,
                sum((w.cost for w in trace), F(0)),
                sum(w.span for w in trace), trace)
    return validate(fragment._replace(edges=fragment.edges + (edge,)))


def donor(cost):
    windows = (Window(cost, 1),)
    return Part((0, 1, 2), (Edge(0, 1, cost, 1, windows),
                            Edge(1, 2, cost, 1, windows)),
                Port(0, "in", "window"), Port(2, "out", "window"))


def attach(fragment, boundary, part, mapping):
    compatible(boundary, part)
    validate(Graph(part.vertices, part.edges, fragment.capacity,
                   part.entry.vertex, part.exit.vertex, fragment.horizon))
    require(set(mapping) == set(part.vertices), "COMPLETE_MAPPING")
    require(len(set(mapping.values())) == len(mapping), "INJECTIVE_MAPPING")
    require(mapping[part.entry.vertex] == boundary.outgoing.vertex
            and mapping[part.exit.vertex] == boundary.incoming.vertex, "MAPPED_PORTS")
    internal = set(part.vertices) - {part.entry.vertex, part.exit.vertex}
    require(all(mapping[v] not in fragment.vertices for v in internal), "FRESH_INTERNAL")
    vertices = fragment.vertices + tuple(mapping[v] for v in part.vertices if v in internal)
    edges = fragment.edges + tuple(e._replace(source=mapping[e.source], target=mapping[e.target])
                                  for e in part.edges)
    return validate(fragment._replace(vertices=vertices, edges=edges))


def shape(graph):
    return (graph.vertices, tuple((e.source, e.target) for e in graph.edges),
            graph.start, graph.goal, graph.horizon, graph.capacity)


def trace_of(graph, path):
    return tuple(w for edge in edges_of(graph, path) for w in edge.trace)


def first_crossing(trace, capacity):
    burden, elapsed = F(0), 0
    for window in trace:
        burden += window.cost
        elapsed += window.span
        if burden >= capacity:
            return elapsed
    return None


def to_xv(graph, data):
    validate(graph)
    return data["base"].api.nest.Sub(
        graph.vertices, [(e.source, e.target) for e in graph.edges],
        {i: e.cost for i, e in enumerate(graph.edges)}, graph.capacity)


def ie_for(graph, path, data):
    base = data["base"]
    upper = base.stitch.to_xiv_sub(to_xv(graph, data), base.api)
    try:
        lower, inclusion = base.stitch.construct_lower(upper, path, base.api)
        return base.stitch.verify_constructed_ie(upper, lower, inclusion, path, base.api)
    except base.stitch.Refusal as exc:
        return {"verdict": str(exc)}


def globally_nestable(graph, data):
    return data["base"].api.nest.is_nestable(to_xv(graph, data))


def fixture(root=None):
    """Read the actual pinned accounting carrier; attach declared window spans."""
    import identity_stitch
    import poa_stitch
    base = poa_stitch.load_sources(Path(root) if root is not None else Path(__file__).resolve().parent)
    windows = [([j], {j: F(1, 3)}) for j in range(4)]
    upper, gamma = identity_stitch.accounting_substrate(base, windows, F(2))
    pairs = tuple(zip(gamma, gamma[1:]))
    require(set(upper.X) == set(gamma), "SOURCE_VERTEX_SET")
    require(set(upper.E) == set(pairs), "SOURCE_EDGE_SET")
    edges = tuple(Edge(u, v, upper.phi_edge((u, v)), 1,
                       (Window(upper.phi_edge((u, v)), 1),)) for u, v in pairs)
    graph = validate(Graph(tuple(gamma), edges, upper.C, gamma[0], gamma[-1], 4))
    require(all(e.cost == F(1, 3) for e in graph.edges), "ACTUAL_EDGE_COSTS")
    return {"base": base, "poa": base.poa, "commits": base.commits,
            "source_provenance": base.provenance, "graph": graph}


def cases(data):
    original = data["graph"]
    fragment, boundary = cut(original)
    mapping = {0: 1, 1: 5, 2: 3}
    return original, fragment, boundary, fold(fragment, boundary), (
        attach(fragment, boundary, donor(F(1, 6)), mapping)), (
        attach(fragment, boundary, donor(F(1)), mapping))


def rejected(function, marker):
    try:
        function()
    except Refusal as exc:
        return str(exc) == marker
    except Exception:
        return False
    return False


def teeth(data):
    original, fragment, boundary, folded, cheap, costly = cases(data)
    failed = []
    seen = []
    def check(name, condition):
        seen.append(name)
        print(("ok " if condition else "FAIL ") + name)
        if not condition:
            failed.append(name)

    source_route = routes(original)[0]
    check("actual_source_burden",
          source_route == ((0, 1, 2, 3, 4), F(4, 3), 4)
          and original.capacity - source_route[1] == F(2, 3))
    extra = original._replace(edges=original.edges + (Edge(2, 0, F(0), 1, (Window(F(0), 1),)),))
    check("excision_breaks_route",
          2 not in fragment.vertices and not routes(fragment)
          and rejected(lambda: cut(extra), "UNDECLARED_BOUNDARY_CONTACT")
          and rejected(lambda: cut(original, (1, 4, 3)), "DECLARED_COMPONENT_PATH"))
    folded_route = routes(folded)[0]
    check("fold_preserves_burden",
          folded_route[1] == F(4, 3) and folded.capacity - folded_route[1] == F(2, 3))
    check("fold_preserves_declared_span",
          folded_route[2] == 4 and len(folded_route[0]) - 1 == 3
          and edges_of(folded, (1, 3))[0].span == 2)
    check("donor_changes_pattern",
          routes(cheap) == (((0, 1, 5, 3, 4), F(1), 4),)
          and 5 in cheap.vertices and 2 not in cheap.vertices)
    check("reachable_route_can_exhaust_budget",
          routes(costly) == (((0, 1, 5, 3, 4), F(8, 3), 4),)
          and costly.capacity - routes(costly)[0][1] == F(-2, 3)
          and not functional(costly) and functional(cheap) and functional(original))

    wrong = boundary._replace(incoming=Port(3, "in", "other"))
    reversed_port = boundary._replace(outgoing=Port(1, "in", "window"))
    check("port_contract_rejects",
          rejected(lambda: fold(fragment, wrong), "BOUNDARY_PORTS")
          and rejected(lambda: fold(fragment, reversed_port), "BOUNDARY_PORTS")
          and rejected(lambda: attach(fragment, boundary,
              donor(F(1, 6))._replace(entry=Port(0, "out", "window")),
              {0: 1, 1: 5, 2: 3}), "DONOR_PORTS")
          and rejected(lambda: attach(fragment, boundary,
              donor(F(1, 6))._replace(exit=Port(2, "out", "other")),
              {0: 1, 1: 5, 2: 3}), "DONOR_PORTS"))
    part = donor(F(1, 6))
    check("attachment_mapping_rejects",
          rejected(lambda: attach(fragment, boundary, part, {0: 1, 2: 3}), "COMPLETE_MAPPING")
          and rejected(lambda: attach(fragment, boundary, part, {0: 1, 1: 1, 2: 3}),
                       "INJECTIVE_MAPPING")
          and rejected(lambda: attach(fragment, boundary, part, {0: 0, 1: 5, 2: 3}),
                       "MAPPED_PORTS")
          and rejected(lambda: attach(fragment, boundary, part, {0: 1, 1: 4, 2: 3}),
                       "FRESH_INTERNAL"))

    omega = (cheap, costly)
    decide = lambda observation, target: data["poa"].fibre_decision(
        omega, observation, functional, observation(target))
    check("observation_preserved_loss_unknown",
          shape(cheap) == shape(costly) and decide(lambda g: g, cheap) == data["poa"].GateEmission.ADMIT
          and decide(lambda g: g, costly) == data["poa"].GateEmission.REJECT and decide(shape, cheap) == data["poa"].GateEmission.INSUFFICIENT)
    folded_ie = ie_for(folded, folded_route[0], data)
    cheap_ie = ie_for(cheap, routes(cheap)[0][0], data)
    costly_ie = ie_for(costly, routes(costly)[0][0], data)
    check("real_xiv_xv_ie",
          folded_ie["verdict"] == "NESTED-BOUNDARY" and folded_ie["m_IE"] == "0"
          and folded_ie["steps"] == 3 and cheap_ie["verdict"] == "NESTED-BOUNDARY"
          and cheap_ie["m_IE"] == "0" and cheap_ie["steps"] == 4
          and costly_ie["verdict"] == "UPPER_SUBCRITICAL_REQUIRED")
    check("route_loss_not_global_non_nestability",
          not functional(costly) and globally_nestable(costly, data)
          and ie_for(costly, (0, 1), data)["verdict"] == "NESTED-BOUNDARY")

    e = original.edges[0]
    invalid = (
        (original._replace(vertices=original.vertices + (0,)), "VERTEX_SET"),
        (original._replace(start=8), "ENDPOINTS"),
        (original._replace(capacity=F(0)), "CAPACITY"),
        (original._replace(horizon=0), "HORIZON"),
        (original._replace(edges=original.edges + (e,)), "UNIQUE_EDGES"),
        (original._replace(edges=(e._replace(target=8),)), "EDGE_ENDPOINT"),
        (original._replace(edges=(e._replace(cost=-F(1)),)), "EXACT_NONNEGATIVE_COST"),
        (original._replace(edges=(e._replace(cost=1.0, trace=(Window(F(1), 1),)),)), "EXACT_NONNEGATIVE_COST"),
        (original._replace(edges=(e._replace(span=0),)), "POSITIVE_SPAN"),
        (original._replace(edges=(e._replace(span=1.0),)), "POSITIVE_SPAN"),
        (original._replace(edges=(e._replace(trace=(Window(F(1), 1),)),)), "TRACE_ACCOUNTING"),
    )
    check("graph_contract_refuses_invalid",
          all(rejected(lambda g=g: validate(g), marker) for g, marker in invalid))
    check("declared_horizon_enforced",
          not routes(folded._replace(horizon=3))
          and rejected(lambda: validate(folded._replace(horizon=True)), "HORIZON"))
    check("strict_budget_boundary", not functional(original._replace(capacity=F(4, 3))))
    a = (Window(F(1, 3), 1), Window(F(2, 3), 1))
    b = tuple(reversed(a))
    aggregate = lambda h: (sum(w.cost for w in h), sum(w.span for w in h))
    first_window = lambda h: first_crossing(h, F(1, 2)) == 1
    early = data["poa"].fibre_decision((a, b), aggregate, first_window, aggregate(a))
    budget = data["poa"].fibre_decision(
        (a, b), aggregate, lambda h: sum(w.cost for w in h) < F(1, 2), aggregate(a))
    nonuniform = original._replace(edges=tuple(
        e._replace(cost=F(2, 3), trace=(Window(F(2, 3), 1),))
        if (e.source, e.target) == (2, 3) else e for e in original.edges))
    varied_fragment, varied_boundary = cut(nonuniform)
    varied_fold = fold(varied_fragment, varied_boundary)
    check("trajectory_order_not_aggregate",
          sum(w.cost for w in a) == sum(w.cost for w in b)
          and sum(w.span for w in a) == sum(w.span for w in b)
          and first_crossing(a, F(1, 2)) == 2 and first_crossing(b, F(1, 2)) == 1
          and trace_of(folded, folded_route[0]) == trace_of(original, source_route[0])
          and trace_of(varied_fold, (0, 1, 3, 4)) == trace_of(nonuniform, source_route[0])
          and early == data["poa"].GateEmission.INSUFFICIENT
          and budget == data["poa"].GateEmission.REJECT)
    report_key = "fold_retains_ordered_window_trace"
    varied_data = dict(data, graph=nonuniform)
    healthy_report = result(data)[report_key]
    varied_report = result(varied_data)[report_key]
    real_fold = fold
    def reverse_windows(graph, ports):
        return real_fold(graph, ports._replace(trace=tuple(reversed(ports.trace))))
    with patch.dict(globals(), fold=reverse_windows):
        broken_report = result(varied_data)[report_key]
    branched = validate(nonuniform._replace(edges=nonuniform.edges + (
        Edge(0, 4, F(1, 4), 1, (Window(F(1, 4), 1),)),)))
    branched_fragment, branched_boundary = cut(branched)
    reordered_fold = real_fold(branched_fragment, branched_boundary)
    reordered_fold = reordered_fold._replace(edges=tuple(reversed(reordered_fold.edges)))
    before_order = tuple(trace_of(branched, p) for p, _, _ in routes(branched))
    after_order = tuple(trace_of(reordered_fold, p) for p, _, _ in routes(reordered_fold))
    def reorder_edges(graph, ports):
        built = real_fold(graph, ports)
        return built._replace(edges=tuple(reversed(built.edges)))
    with patch.dict(globals(), fold=reorder_edges):
        reordered_report = result(dict(data, graph=branched))[report_key]
    check("report_trace_is_derived", healthy_report is True and varied_report is True
          and broken_report is False and reordered_report is True
          and before_order != after_order and Counter(before_order) == Counter(after_order))
    # The printed count reports executed checks, not only the declared constant.
    require(EXPECTED_TEETH == 16 and len(seen) == 16 and len(set(seen)) == 16, "TEETH_COUNT")
    print("teeth: %d/%d" % (EXPECTED_TEETH - len(failed), EXPECTED_TEETH))
    return not failed


def result(data):
    original, fragment, boundary, folded, cheap, costly = cases(data)
    rows = {}
    for name, graph in (("original", original), ("cut", fragment),
                        ("fold", folded), ("cheap", cheap), ("costly", costly)):
        found = routes(graph)
        row = {"complete_routes": [{"path": path, "burden": str(cost), "window_span": span,
                "margin": str(graph.capacity - cost)} for path, cost, span in found],
               "declared_endpoint_function": functional(graph)}
        if found:
            row["requested_route_IE"] = ie_for(graph, found[0][0], data)
            row["global_XV_nestable"] = globally_nestable(graph, data)
        rows[name] = row
    omega = (cheap, costly)
    rows["observation"] = {name: data["poa"].fibre_decision(
        omega, observe, functional, observe(target)).value
        for name, observe, target in (("cheap_full", lambda g: g, cheap),
          ("costly_full", lambda g: g, costly), ("shape_only", shape, cheap))}
    return {"scope": "Finite declared chain interfaces; window spans are auxiliary.",
            "commits": data["commits"], "source_provenance": data["source_provenance"], "cases": rows,
            "identity_for_new_graph": "not_established",
            "fold_retains_ordered_window_trace": Counter(
                trace_of(original, path) for path, _, _ in routes(original)) == Counter(
                trace_of(folded, path) for path, _, _ in routes(folded))}


def main(argv=None):
    import identity_stitch
    import tectonica
    argv = sys.argv[1:] if argv is None else argv
    try:
        require(argv in ([], ["--teeth"]), "USAGE: recomposition_stitch.py [--teeth]")
        data = fixture()
        if not teeth(data):
            return 1
        if "--teeth" not in argv:
            print(json.dumps(result(data), indent=2))
            print("RECOMPOSITION_CONNECTION: PASS (%d checks; finite declared chain interfaces)"
                  % EXPECTED_TEETH)
        return 0
    except (Refusal, identity_stitch.Refusal, tectonica.Refusal, OSError, ValueError) as exc:
        print("RECOMPOSITION_CONNECTION: REFUSED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
