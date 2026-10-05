"""Selected complete-route projection into a caller-supplied trusted Person API.

Fixed capacity; declared integer window coordinates. No identity verdict.
Final immutable source loading remains the caller's responsibility.
"""
class Refusal(ValueError):
    pass


def project(graph, path, recomposition, person):
    recomposition.validate(graph)
    if type(path) is not tuple or path not in tuple(p for p, _, _ in recomposition.routes(graph)):
        raise Refusal("COMPLETE_SELECTED_ROUTE")
    trace = tuple(person.Window(w.cost, w.span) for w in recomposition.trace_of(graph, path))
    person.validate(trace)
    return trace


def selected_report(graph, path, recomposition, person):
    trace = project(graph, path, recomposition, person)
    return {"capacity": graph.capacity, "trace": trace,
            "prefix_budgets": person.prefix_budgets(trace, graph.capacity),
            "final_survival": person.final_survival(trace, graph.capacity),
            "whole_survival": person.whole_survival(trace, graph.capacity),
            "first_crossing": person.first_crossing(trace, graph.capacity)}


def compare(before, before_path, after, after_path, recomposition, person):
    if before.capacity != after.capacity:
        raise Refusal("FIXED_CAPACITY_CONTEXT")
    old = project(before, before_path, recomposition, person)
    new = project(after, after_path, recomposition, person)
    return person.loss_status(old, new, before.capacity)
