"""Native V4 P4 cradle and its four keeper plates, in assembly coordinates.

Dimensions follow 01_geometry.py. All profiles and holes are CAD geometry;
there is no mesh or STL input. Units are millimetres.
"""
import cadquery as cq

from native_common import rect, cyl, union, cut


TRAY_SCREWS = ((13.0, -10.0), (37.7, -10.0), (13.0, 15.0), (37.7, 15.0))


def build_parts() -> list[tuple[str, cq.Shape]]:
    tray = rect(28.6, 45.0, 4.0, 5.2, 26.1, -1.5, 1.0)
    for x, y in TRAY_SCREWS:
        tray = union(tray, cyl(2.6, 4.0, 5.2, x, y))
        tray = cut(tray, cyl(1.35, 3.7, 5.7, x, y))

    for y in (-18.0, 12.0):
        for x in (14.0, 37.8):
            width = 5.0 if x == 14.0 else 4.6
            tray = union(tray, rect(width, 10.0, 5.0, 9.3, x, y, .5))
            step_x, step_width, screw_x = (
                (13.65, 3.3, 14.0) if x == 14.0 else (38.4, 3.4, 38.0)
            )
            tray = union(tray, rect(step_width, 10.0, 9.1, 13.85, step_x, y, .35))
            tray = cut(tray, cyl(.85, 6.3, 14.1, screw_x, y))

    for x in (17.11, 34.89):
        tray = cut(tray, rect(1.6, 52.0, 3.5, 12.5, x, -7.8, .2))

    keeper = rect(4.4, 10.0, 13.85, 15.05, 14.0, -18.0, .4)
    keeper = cut(keeper, cyl(1.1, 13.5, 15.4, 14.0, -18.0))
    return [
        ('P10_board_cradle', tray),
        ('P11_board_keeper', keeper),
        ('P11_board_keeper_2', keeper.translate((0.0, 30.0, 0.0))),
        ('P11_board_keeper_3', keeper.translate((24.0, 0.0, 0.0))),
        ('P11_board_keeper_4', keeper.translate((24.0, 30.0, 0.0))),
    ]


if __name__ == '__main__':
    import json
    info = []
    for name, shape in build_parts():
        valid = shape.isValid()
        count = len(shape.Solids())
        volume = shape.Volume()
        assert valid and count == 1 and volume > 0, name
        info.append({'name': name, 'valid': valid, 'solids': count, 'volume_mm3': volume})
    print(json.dumps(info))
