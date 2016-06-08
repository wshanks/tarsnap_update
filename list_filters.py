"""Set of filters for selecting a subset of a list"""


def sort_by_bounds(target, bounds):
    """Sort target into a list of sublists with the distance of all elements in
    one sublist from the first element of target being less than the bound with
    the same index as that sublist (but greater than the previous sublist)
    """
    sorted_target = [[] for dummy in range(len(bounds))]
    for idx, elem in enumerate(target):
        for bound_idx, bound in enumerate(bounds):
            if not bound or abs(elem - target[0]) < bound:
                sorted_target[bound_idx].append(idx)
                break

    return sorted_target


def space_by_span(target, spacing_params):
    """Select entries in target that satisfy the specified spacing_params

    space_by_span examines the elements in target from first to last and
    selects those that are spaced apart enough to satisfy the parameters in
    spacing_params. spacing_params consists of a set of target element spacings
    and target element bounds. For each element, the only spacing/bound pair
    that applies is the one for which that element is closer to the first
    element of target than the bound but not closer than the previous bound
    (the bounds in spacing_params should be in increasing order). The elements
    of target are examined one by one and either selected or not selected. The
    first element is always selected. Subsequently, an element is selected if
    it is at least half a spacing away from the last selected element and is
    the closest element in target to being exactly one spacing away from the
    last selected element.

    target: a list of items that can be subtracted from each other to calculate
        spacings
    spacing_params: a list of 2-element tuples where the first element is a
        spacing and the second element is a bound

    Notes
    * Elements beyond the last bound are not selected.
    * If a bound evaluates to false, its spacing is used for all remaining
    elements not covered by any previous bound.

    return: list of indices of elements from target that were selected
    """
    spacings = [par[0] for par in spacing_params]
    bounds = [par[1] for par in spacing_params]

    sorted_target = sort_by_bounds(target, bounds)

    selected = []
    for idx, subset in enumerate(sorted_target):
        if not subset:
            continue

        spacing = spacings[idx]
        selected.append(subset.pop(0))
        candidate = None
        while subset:
            if not candidate:
                if abs(target[subset[0]] - target[selected[-1]]) > spacing/2:
                    candidate = subset.pop(0)
                else:
                    subset.pop(0)
            else:
                cand_delta = abs(abs(target[candidate] -
                                     target[selected[-1]]) -
                                 spacing)
                next_delta = abs(abs(target[subset[0]] -
                                     target[selected[-1]]) -
                                 spacing)
                if cand_delta > next_delta:
                    candidate = subset.pop(0)
                else:
                    selected.append(candidate)
                    candidate = None
        if candidate:
            selected.append(candidate)

    return selected
