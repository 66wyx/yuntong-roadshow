"""Native CAD controls for RIG-P1 V4, in millimetre assembly coordinates.

Rebuilt from the dimensioned procedural source, without STL or mesh input.
Circular edges and holes are analytic; the bezel uses exact cubic Beziers.
"""
import cadquery as cq
from native_common import (
    rect, cyl, corner_prism, rocker_prism, union, cut, stroke,
)

CASE_SCREWS = [(-39, -30), (-39, 30), (39.8, -40), (39.8, 40)]
KEY_SCREWS = [(21.2, -33), (38, -33), (21.2, 30), (38, 30)]
KEYS = [
    ('up', 30, 16.75, 11.2, 10.9),
    ('down', 30, 5.25, 11.2, 10.9),
    ('confirm', 30, -14, 11.2, 11.2),
    ('mode', 30, -25.5, 8.4, 4.2),
]
ENGRAVINGS = {
    'P05_key_up': [(28, 16), (30, 18), (32, 16)],
    'P06_key_down': [(28, 6), (30, 4), (32, 6)],
    'P07_key_confirm': [(27.8, -14), (29.3, -15.5), (32.4, -12.2)],
}
FILLET_NOTES = {}


def small_top_fillet(name, shape, top_z):
    """Break the visible top edge by a native 0.08 mm rolling-ball fillet.

    Tangential seams and non-horizontal edges are left untouched. A failure
    leaves the exact original dimensions and CAD geometry intact.
    """
    solids = shape.Solids()
    if len(solids) != 1:
        FILLET_NOTES[name] = 'omitted: shape is not one solid'
        return shape
    solid = solids[0]
    edges = []
    for edge in solid.Edges():
        box = edge.BoundingBox()
        if abs(box.zmin - top_z) < 1e-5 and abs(box.zmax - top_z) < 1e-5:
            edges.append(edge)
    if not edges:
        FILLET_NOTES[name] = 'omitted: no top perimeter edges'
        return shape
    try:
        candidate = solid.fillet(0.08, edges)
        if candidate.isValid() and len(candidate.Solids()) == 1:
            FILLET_NOTES[name] = 'native 0.08 mm top edge fillet applied'
            return candidate
    except Exception as error:
        FILLET_NOTES[name] = 'omitted: ' + str(error)[:160]
        return shape
    FILLET_NOTES[name] = 'omitted: fillet result invalid'
    return shape


def build_parts():
    parts = []
    bezel = corner_prism(57.6, 88, 4.5, 25.65, 26.85, -11, 0)
    bezel = cut(bezel, rect(44.2, 58.6, 25.2, 27.2, -11, -4.9, .35))
    bezel = cut(bezel, rect(50.6, 69.8, 25.4, 25.95, -11, -2, .25))
    bezel = small_top_fillet('P03_black_bezel', bezel, 26.85)
    parts.append(('P03_black_bezel', bezel))

    # Carrier is thinner than V3 and clears the complete 14.5 mm P4 envelope.
    carrier = rect(21.2, 79, 17.6, 18.8, 29.8, 4.5, 1.3)
    carrier = cut(carrier, rect(3, 6, 14, 22, 40, 43, .2))
    for x, y in CASE_SCREWS:
        carrier = cut(carrier, cyl(2.95, 14, 23, x, y))
    for kind, x, y, width, height in KEYS:
        rim = rect(7.8, 7.8, 18.6, 19.9, x, y, .6)
        rim = cut(rim, rect(6.4, 6.4, 18.4, 20.2, x, y, .35))
        carrier = union(carrier, rim)
        for dx in (-2.5, 2.5):
            for dy in (-2.25, 2.25):
                carrier = cut(carrier, cyl(.65, 17.2, 20.1, x + dx, y + dy))
    for x, y in KEY_SCREWS:
        carrier = cut(carrier, cyl(1.1, 17.2, 20.1, x, y))
    carrier = union(carrier, rect(9, 1.7, 14.1, 21.5, 30, 40.3, .4))
    for x in (26.4, 33.6):
        carrier = union(carrier, rect(1.2, 4.5, 14.1, 21.5, x, 42.2, .3))
    parts.append(('P04_key_carrier', carrier))

    for index, (kind, x, y, width, height) in enumerate(KEYS, start=5):
        capw, caph = width - .1, height - .1
        radius = min(capw, caph) / 2 if kind in ('up', 'down', 'confirm') else .8
        if kind in ('up', 'down'):
            cap = rocker_prism(capw, caph, kind == 'up', 23.7, 27.7, x, y)
        else:
            cap = rect(capw, caph, 23.7, 27.7, x, y, radius)
        extra = .4 if kind in ('up', 'down') else 1.4
        cap = union(cap, rect(capw + 1.8, caph + extra, 23.3, 23.85,
                              x, y, min(radius + .4, 3)))
        cap = union(cap, cyl(1.4, 23.2, 24.1, x, y))
        name = 'P%02d_key_%s' % (index, kind)
        points = ENGRAVINGS.get(name, [])
        for a, b in zip(points[:-1], points[1:]):
            cap = cut(cap, stroke(a, b, .55, 27.35, 28))
        cap = small_top_fillet(name, cap, 27.7)
        parts.append((name, cap))

    power = rect(12, 3.1, 15.6, 18.6, 30, 47.25, 1.1)
    power = union(power, rect(14, .8, 15.1, 19.1, 30, 45.1, .3))
    power = union(power, rect(2, 1.4, 16.2, 18, 30, 45.3, .3))
    power = small_top_fillet('P09_top_key', power, 18.6)
    parts.append(('P09_top_key', power))
    return parts


if __name__ == '__main__':
    import json
    result = []
    for name, shape in build_parts():
        result.append({'name': name, 'valid': shape.isValid(),
                       'solids': len(shape.Solids()), 'volume_mm3': shape.Volume()})
        assert shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0, name
    print(json.dumps({'parts': result, 'top_fillets': FILLET_NOTES}, indent=2))
