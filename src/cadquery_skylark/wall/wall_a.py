import cadquery as cq

from .. import details, common


mm = int


def _bowtie_pair_points(width: mm, height: mm):
    for x in (-width / 2, width / 2):
        for y in range(-height // 2 + 300, height // 2, 600):
            yield x, y


def _slot_pairs_points(width: mm, height: mm):
    for x in (-width / 2, width / 2):
        for y in range(-height // 2 + 600, height // 2, 600):
            yield x, y


def _top_and_bottom_bowtie_points(height: mm):
    for x in (-194.9, 0, 194.9):
        for y in (-height / 2, height / 2):
            yield x, y


def _corner_points(width: mm, height: mm, dx: mm = 0, dy: mm = 0):
    for x in (-(width / 2 - dx), width / 2 - dx):
        for y in (-(height / 2 - dy), height / 2 - dy):
            yield x, y


def outside(width: mm, height: mm) -> cq.Sketch:
    sketch = cq.Sketch().rect(width, height)

    sketch.push(_bowtie_pair_points(width, height))
    sketch.face(details.bowtie_pair(), mode="s")

    sketch.push(_slot_pairs_points(width, height))
    sketch.face(details.slot_pair(), mode="s")

    sketch.push(_top_and_bottom_bowtie_points(height))
    sketch.face(details.bowtie(), mode="s")

    sketch.push(_corner_points(width, height))
    sketch.face(details.corner(), mode="s")

    return sketch.reset()


def _middle_hole_points(height: mm):
    for y in range(-height // 2 + 600, height // 2, 600):
        yield 0, y


def inside(height: mm) -> cq.Sketch:
    sketch = cq.Sketch()
    sketch.push(_middle_hole_points(height))
    sketch.face(details.middle_hole())
    return sketch.reset()


def _bowtie_handles(width: mm, height: mm) -> cq.Sketch:
    s = cq.Sketch()
    s.push(_bowtie_pair_points(width, height)).face(details.bowtie_handle_pair())
    s.push(_top_and_bottom_bowtie_points(height)).face(details.bowtie_handle())
    s.push([]).rect(width, height, mode="i")
    return s.reset()


def _slot_trim(width: mm, height: mm) -> cq.Sketch:
    s = cq.Sketch()
    s.push(_slot_pairs_points(width, height)).rect(18 * 2, 62)
    s.push([]).rect(width, height, mode="i")
    s.vertices().fillet(6)
    return s.reset()


def _corner_trim(width: mm, height: mm) -> cq.Sketch:
    s = cq.Sketch()
    s.push(_corner_points(width, height, dy=52.5)).rect(18 * 2, 37)
    s.push([]).rect(width, height, mode="i")
    s.vertices().fillet(6)
    return s.reset()


def half_depth(width: mm, height: mm) -> cq.Sketch:
    bowtie_handles = _bowtie_handles(width, height)
    slot_trim = _slot_trim(width, height)
    corner_trim = _corner_trim(width, height)
    return cq.Sketch().face(bowtie_handles).face(slot_trim).face(corner_trim)


def make_part(height: mm) -> cq.Solid:
    width = 600
    outside_s = outside(width, height)
    inside_s = inside(height)
    half_s = half_depth(width, height)

    p = cq.Workplane("XY").placeSketch(outside_s).extrude(18)
    p = p.faces(">Z").workplane(centerOption="CenterOfBoundBox")
    p = p.placeSketch(inside_s).cutThruAll()
    p = p.faces(">Z").workplane(centerOption="CenterOfBoundBox")
    p = p.placeSketch(half_s).cutBlind(-18 / 2)

    return common.recenter(p.findSolid())


def make_cnc(height: mm):
    width = 600
    blue = outside(width, height).wires().offset(-0.25, mode="i").reset().clean()
    cyan = inside(height).wires().offset(0.25, mode="a").reset().clean()
    green = half_depth(width, height).wires().offset(0.25, mode="a").reset().clean()
    return blue, cyan, green
