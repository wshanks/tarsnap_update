"""Set of filters for selecting a subset of a list"""

#  This file is part of tarsnap_update
#
# tarsnap_update is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# tarsnap_update is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2016, willsALMANJ


def spacing_lookup(distance, spacing_params):
    '''Determine the spacing that applies for distance

    distance is compared to the bounds in spacing_params. The spacing
    associated with the smallest bound greater than distance is returned.
    '''
    spacing = None
    for spacing, bound in spacing_params:
        if distance < bound:
            break
    return spacing


def eligible_followers(target, index, spacing_params):
    '''Find elements within spacing of element of target

    target -- list of elements
    index -- starting index to compare subsequent elements to
    spacing_params -- spacing params list

    Elements following index are examined to see if they want the same spacing
    as index and, if so, if they are within spacing of index.'''
    followers = []
    cur_spacing = spacing_lookup(abs(target[index] - target[0]),
                                 spacing_params)
    for jdx in range(index+1, len(target)):
        j_spacing = spacing_lookup(abs(target[jdx] - target[0]),
                                   spacing_params)

        j_distance = abs(target[jdx] - target[index])

        # Extra 5% cushion to avoid edge cases
        if j_spacing == cur_spacing and j_distance < 1.05*cur_spacing:
            followers.append(jdx)
        else:
            break

    return followers


def space_by_span(target, spacing_params, reverse=False):
    """Select entries in target that satisfy the specified spacing_params

    space_by_span examines the elements in target from first to last and
    selects those that are spaced apart enough to satisfy the parameters in
    spacing_params. spacing_params consists of a set of target element spacings
    and target element bounds. For each element, the only spacing/bound pair
    that applies is the one with the smallest bound that is greater than the
    distance from the element to the first element of target.

    The elements of target are examined one by one and either selected or not
    selected. The first element and last element for each spacing are always
    selected. Elements subsequent to the first in a spacing set are selected if
    they are the closest to being one spacing away from the previous element
    (without being more than 1.05 * spacing away; the 5% extra is to allow for
    some tolerance of edge cases).

    target: a list of items that can be subtracted from each other to calculate
        spacings
    spacing_params: a list of 2-element tuples where the first element is a
        spacing and the second element is a bound. The list should be ordered
        from smallest to largest spacings and bounds.
    reverse: target is copied and sorted inside the function before applying
        spacings. reverse sets whether or not the list is reversed after
        sorting.

    return: list of indices of elements from target that were selected

    Notes
    * The last spacing applies to all elements that do not match the earliera
    spacings even if those elements are outside the last bound
    * If the spacings in target are very different from the spacings in
    spacing_params, the resulting subset of target might have a fairly
    different spacing from the spacing params. This is a consequence of always
    trying to save one subsequent item within a spacing of the last item, even
    if the two are close. This behavior was chosen because it is more
    conservative than trying to maintain the spacing as closely as possible
    (which can have the side effect of throwing out all elements as they cross
    a certain bound when space_by_span is called repeatedly on a list each time
    a new element is added to the beginning of it).
    """
    sorted_target = sorted(enumerate(target), key=lambda x: x[1],
                           reverse=reverse)
    orig_indices = [elem[0] for elem in sorted_target]
    target = [elem[1] for elem in sorted_target]

    # Always keep first element
    keep = [0]
    while keep[-1] < len(target) - 1:
        # Get elements within spacing
        spacing = spacing_lookup(abs(target[keep[-1]] - target[keep[0]]),
                                 spacing_params)
        followers = eligible_followers(target, keep[-1], spacing_params)

        # Choose element
        if followers:
            distance = [(f, abs(spacing - abs(target[keep[-1]] - target[f])))
                        for f in followers]
            distance.sort(key=lambda x: x[1])
            keep.append(distance[0][0])
        else:
            keep.append(keep[-1] + 1)

    return [orig_indices[idx] for idx in keep]
