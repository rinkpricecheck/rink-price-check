#!/usr/bin/env python3
"""Combine per-colour STL files into one multicolour 3MF.

Each colour becomes its own coloured part, all grouped into a single object,
laid flat with the front facing up, so a multicolour slicer (Bambu Studio, OrcaSlicer, PrusaSlicer) loads them
aligned and you only assign a filament to each part.

usage: make_3mf.py [--bambu] OUT.3mf NAME colour=file.stl [colour=file.stl ...]
       a part can be written label@colour=file.stl to make it its own named part
       (e.g. miami@black=... shows up as "MIAMI" on the black filament)

--bambu writes a Bambu Studio project instead: each part is pre-assigned to
filament 1..N with the right colour, so Bambu skips its "Simplify Colors" /
"Filament Matching" import dialog.
"""
import json
import sys
import zipfile

import numpy as np

COLOURS = {
    "black": "#141414", "yellow": "#FADB1A", "cream": "#EDE6D1", "red": "#D9261F",
    "white": "#F7F7F7", "orange": "#F78C1F", "pink": "#F26B8C",
}


def spec(s):
    """'label@colour' -> (part name, filament colour); a plain colour is both."""
    label, _, colour = s.partition("@")
    return (label.upper(), colour) if colour else (s, s)


def read_stl(path):
    """Return (vertices Nx3, triangles Mx3) from an ASCII or binary STL."""
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        pts = [l.split()[1:4] for l in data.decode().splitlines() if l.strip().startswith("vertex")]
        tri = np.array(pts, dtype=np.float64)
    else:
        n = int.from_bytes(data[80:84], "little")
        rec = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype(
            [("n", "<f4", 3), ("v", "<f4", 9), ("a", "<u2")]))
        tri = rec["v"].reshape(-1, 3).astype(np.float64)
    verts, idx = np.unique(np.round(tri, 5), axis=0, return_inverse=True)
    faces = idx.reshape(-1, 3)
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    return verts, faces


def mesh_xml(verts, faces):
    v = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in verts)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return f"<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh>"


def main():
    args = sys.argv[1:]
    bambu = args[0] == "--bambu"
    if bambu:
        args = args[1:]
    out, name, pairs = args[0], args[1], [a.split("=", 1) for a in args[2:]]
    meshes = [(c, *read_stl(p)) for c, p in pairs]
    fil = list(dict.fromkeys(spec(c)[1] for c, *_ in meshes))           # filament slots, in order
    # lay flat for printing: the front face (-Y in the CAD files) turns to face up (+Z)
    meshes = [(c, np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]), f) for c, v, f in meshes]
    lo = np.min([m[1].min(0) for m in meshes], axis=0)
    hi = np.max([m[1].max(0) for m in meshes], axis=0)
    shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])   # centre, sit on the bed

    n = len(meshes)
    gid = n + 2
    objs, comps = [], []
    for i, (c, v, f) in enumerate(meshes):
        oid = i + 2
        mat = "" if bambu else f' pid="1" pindex="{i}"'
        objs.append(f'<object id="{oid}" name="{name} - {spec(c)[0]}" type="model"{mat}>{mesh_xml(v + shift, f)}</object>')
        comps.append(f'<component objectid="{oid}"/>')
    if bambu:
        head = ('xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">'
                '<metadata name="Application">BambuStudio-01.08.00.00</metadata>'
                '<metadata name="BambuStudio:3mfVersion">1</metadata>')
        mats, item = "", f'<item objectid="{gid}" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/>'
    else:
        head = ">"
        mats = ('<basematerials id="1">' + "".join(
            f'<base name="{spec(c)[0]}" displaycolor="{COLOURS.get(spec(c)[1], "#808080")}FF"/>' for c, *_ in meshes) + "</basematerials>")
        item = f'<item objectid="{gid}"/>'
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" ' + head +
             f'<metadata name="Title">{name}</metadata><resources>{mats}{"".join(objs)}'
             f'<object id="{gid}" name="{name}" type="model"><components>{"".join(comps)}</components></object>'
             f'</resources><build>{item}</build></model>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        if bambu:
            parts = "".join(
                f'<part id="{i + 2}" subtype="normal_part"><metadata key="name" value="{spec(c)[0]}"/>'
                f'<metadata key="extruder" value="{fil.index(spec(c)[1]) + 1}"/></part>' for i, (c, *_) in enumerate(meshes))
            cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>'
                   f'<object id="{gid}"><metadata key="name" value="{name}"/><metadata key="extruder" value="1"/>'
                   f'{parts}</object>'
                   '<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value=""/>'
                   '<metadata key="locked" value="false"/><model_instance>'
                   f'<metadata key="object_id" value="{gid}"/><metadata key="instance_id" value="0"/>'
                   '<metadata key="identify_id" value="100"/></model_instance></plate>'
                   f'<assemble><assemble_item object_id="{gid}" instance_id="0" '
                   'transform="1 0 0 0 1 0 0 0 1 128 128 0" offset="0 0 0"/></assemble></config>')
            z.writestr("Metadata/model_settings.config", cfg)
            z.writestr("Metadata/project_settings.config", json.dumps({
                "filament_colour": [COLOURS.get(c, "#808080") for c in fil],
                "filament_type": ["PLA"] * len(fil),
                "filament_settings_id": ["Generic PLA"] * len(fil),
                "version": "01.08.00.00",
            }, indent=4))
    size = hi - lo
    print(f"{out}: {len(meshes)} parts, {size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} mm")


if __name__ == "__main__":
    main()
