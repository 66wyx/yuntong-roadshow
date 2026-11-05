"""Native CAD reconstruction of V4 front shell and rear cover.

All dimensions are millimetres and follow 01_geometry.py. The native_common
helpers construct analytic cylinders/arcs and exact cubic Bezier profiles;
no render mesh or STL geometry is read by this module.
"""
import cadquery as cq
from native_common import (
    rect, cyl, corner_prism, rocker_prism, side_rect, side_hole,
    cone_z, union, cut, rotate_x_about_origin, stroke,
)

CASE_SCREWS = [(-39, -30), (-39, 30), (39.8, -40), (39.8, 40)]
LCD_HOLES = [(-33, -40), (11, -40), (-33, 36.08), (11, 36.08)]
TRAY_SCREWS = [(13, -10), (37.7, -10), (13, 15), (37.7, 15)]
KEY_SCREWS = [(21.2, -33), (38, -33), (21.2, 30), (38, 30)]
KEYS = [
    ('up', 30, 16.75, 11.2, 10.9),
    ('down', 30, 5.25, 11.2, 10.9),
    ('confirm', 30, -14, 11.2, 11.2),
    ('mode', 30, -25.5, 8.4, 4.2),
]


def build_front_shell():
    """P01: shell, exact corner curves, bosses, apertures and face grooves."""
    shell = corner_prism(86, 96, 8.5, 2.7, 27)
    shell = cut(shell, corner_prism(81.2, 91.2, 6.1, 2, 24))
    shell = cut(shell, corner_prism(58.2, 88.6, 4.8, 25.5, 28, -11, 0))
    shell = cut(shell, rect(44.4, 58.8, 23.8, 28, -11, -4.9, .35))
    shell = cut(shell, rect(50.6, 69.8, 21.4, 25.95, -11, -2, .25))

    for x, y in CASE_SCREWS:
        shell = union(shell, cyl(2.6, 2.7, 25.5, x, y))
        shell = cut(shell, cyl(1.05, 2.3, 16, x, y))
    for x, y in LCD_HOLES:
        shell = union(shell, cyl(2.3, 21.5, 25.5, x, y))
        shell = cut(shell, cyl(1.05, 21, 25.1, x, y))
    for x, y in KEY_SCREWS:
        shell = union(shell, cyl(2.2, 18.8, 25, x, y))
        shell = cut(shell, cyl(.85, 18, 23.8, x, y))

    for kind, x, y, width, height in KEYS:
        if kind in ('up', 'down'):
            aperture = rocker_prism(width+.6, height+.6, kind == 'up', 23.8, 28.5, x, y)
        else:
            aperture = rect(width+.6, height+.6, 23.8, 28.5, x, y,
                            5.6 if kind == 'confirm' else .9)
        shell = cut(shell, aperture)
    shell = cut(shell, rect(12.6, 8, 15, 19.2, 30, 47, 1))
    shell = cut(shell, side_rect(10.2, 4.8, -49, -44.9, 0, 13.5, 2))
    for x in (-8, 8):
        shell = cut(shell, side_hole(1.1, -48.5, -44.8, x, 13.5))
        countersink = rotate_x_about_origin(cone_z(1.1, 2.2, 46.9, 48.1, x, 0), 90, 13.5)
        shell = cut(shell, countersink)

    for y in (30.8, -33.5):
        shell = cut(shell, stroke((20.3, y), (39.5, y), .35, 26.73, 27.15))
    return shell


def build_rear_cover():
    """P02: rear plate, register lip, recessed screw heads and ventilation."""
    back = corner_prism(86, 96, 8.5, 0, 2.4)
    lip = corner_prism(80.6, 90.6, 5.8, 2.2, 3.9)
    lip = cut(lip, corner_prism(78.6, 88.6, 4.8, 2, 4.1))
    for x, y in CASE_SCREWS:
        lip = cut(lip, cyl(2.95, 1.9, 4.2, x, y))
    back = union(back, lip)
    for x, y in CASE_SCREWS:
        back = cut(back, cyl(1.45, -.3, 4.1, x, y))
        back = cut(back, cyl(2.65, -.2, 1.6, x, y))
    for x, y in TRAY_SCREWS:
        back = union(back, cyl(2.6, 2.1, 4, x, y))
        back = cut(back, cyl(1.05, 1.15, 4.2, x, y))
    for y in (-15, -10, -5, 0, 5, 10):
        back = cut(back, rect(25, 1.25, -.2, 2.8, -16, y, .6))
    return back


def build_parts():
    return [
        ('P01_front_shell', build_front_shell()),
        ('P02_rear_cover', build_rear_cover()),
    ]


if __name__ == '__main__':
    for name, shape in build_parts():
        bounds = shape.BoundingBox()
        print(name, 'valid=', shape.isValid(), 'solids=', len(shape.Solids()),
              'volume_mm3=', shape.Volume(),
              'size_mm=', (bounds.xlen, bounds.ylen, bounds.zlen), flush=True)
