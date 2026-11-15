#!/usr/bin/env python3
"""Build a two-plate Bambu Studio project from split per-colour STLs.

Plate 1: front half of the sign + front half of the stick bracket (+ alignment keys)
Plate 2: back half of the sign  + back half of the stick bracket
Each half is laid with its cut face on the bed and its detail facing up, and
every colour part is pre-assigned to its own filament slot.

usage: make_plates.py OUT.3mf NAME colour1,colour2,... STL_DIR
       STL_DIR holds {front,back}_{sign,stick,keys}_{colour}.stl (missing ones are skipped)
       a colour can be label@colour (e.g. miami@black): read from ..._miami.stl, its own
       part named MIAMI on the black filament
"""
import json
import os
import sys
import zipfile

import numpy as np

from make_3mf import COLOURS, mesh_xml, read_stl, spec

BED = 256.0                     # Bambu X1 / P1 / P2S bed; plates sit side by side
STRIDE = BED * 1.2              # Bambu leaves a 1/5 bed gap between plates


def lay_flat(v, half):
    """Cut face (y = 0) down on the bed, detail up. Both are proper rotations."""
    if half == "front":   # -Y face up
        return np.column_stack([v[:, 0], v[:, 2], -v[:, 1]])
    return np.column_stack([v[:, 0], -v[:, 2], v[:, 1]])   # +Y face up


def main():
    out, name, colours, d = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4]
    fil = list(dict.fromkeys(spec(c)[1] for c in colours))
    objects, nid = [], 1          # (plate, label, [(colour, verts, faces)], size)
    for p, half in enumerate(["front", "back"]):
        for piece in ["sign", "stick", "keys"]:
            parts = []
            for c in colours:
                f = os.path.join(d, f"{half}_{piece}_{c.split('@')[0]}.stl")
                if os.path.exists(f) and os.path.getsize(f) > 200:
                    v, tri = read_stl(f)
                    parts.append((c, lay_flat(v, half), tri))
            if not parts:
                continue
            lo = np.min([q[1].min(0) for q in parts], axis=0)
            hi = np.max([q[1].max(0) for q in parts], axis=0)
            shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
            parts = [(c, v + shift, tri) for c, v, tri in parts]
            objects.append((p, f"{name} - {half} {piece}", parts, hi - lo))

    res, items, cfg_objs, plates, assemble = [], [], [], {}, []
    ident = 100
    cur_plate, y, prev_h = None, 0.0, None
    for p, label, parts, size in objects:
        comps, cfg_parts = [], []
        for c, v, tri in parts:
            nid += 1
            res.append(f'<object id="{nid}" name="{label} - {spec(c)[0]}" type="model">{mesh_xml(v, tri)}</object>')
            comps.append(f'<component objectid="{nid}"/>')
            cfg_parts.append(f'<part id="{nid}" subtype="normal_part"><metadata key="name" value="{spec(c)[0]}"/>'
                             f'<metadata key="extruder" value="{fil.index(spec(c)[1]) + 1}"/></part>')
        nid += 1
        gid = nid
        res.append(f'<object id="{gid}" name="{label}" type="model"><components>{"".join(comps)}</components></object>')
        # stack the plate's items top to bottom from the middle (press Arrange in Bambu to repack)
        if p != cur_plate:
            cur_plate, y, prev_h = p, BED / 2, None
        else:
            y -= prev_h / 2 + size[1] / 2 + 10
        prev_h = size[1]
        tf = f"1 0 0 0 1 0 0 0 1 {p * STRIDE + BED / 2:.3f} {y:.3f} 0"
        items.append(f'<item objectid="{gid}" transform="{tf}" printable="1"/>')
        cfg_objs.append(f'<object id="{gid}"><metadata key="name" value="{label}"/>'
                        f'<metadata key="extruder" value="1"/>{"".join(cfg_parts)}</object>')
        ident += 1
        plates.setdefault(p, []).append(
            f'<model_instance><metadata key="object_id" value="{gid}"/><metadata key="instance_id" value="0"/>'
            f'<metadata key="identify_id" value="{ident}"/></model_instance>')
        assemble.append(f'<assemble_item object_id="{gid}" instance_id="0" transform="{tf}" offset="0 0 0"/>')
        print(f"  plate {p + 1}: {label}: {len(parts)} colours, {size[0]:.0f} x {size[1]:.0f} x {size[2]:.1f} mm")

    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">'
             '<metadata name="Application">BambuStudio-01.08.00.00</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata>'
             f'<metadata name="Title">{name}</metadata>'
             f'<resources>{"".join(res)}</resources><build>{"".join(items)}</build></model>')
    plate_xml = "".join(
        f'<plate><metadata key="plater_id" value="{p + 1}"/><metadata key="plater_name" value="'
        f'{"Front halves" if p == 0 else "Back halves"}"/><metadata key="locked" value="false"/>{"".join(m)}</plate>'
        for p, m in sorted(plates.items()))
    cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg_objs) + plate_xml +
           f'<assemble>{"".join(assemble)}</assemble></config>')
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
        z.writestr("Metadata/model_settings.config", cfg)
        z.writestr("Metadata/project_settings.config", json.dumps({
            "filament_colour": [COLOURS[c] for c in fil],
            "filament_type": ["PLA"] * len(fil),
            "filament_settings_id": ["Generic PLA"] * len(fil),
            "version": "01.08.00.00",
        }, indent=4))
    print(f"{out}: {len(objects)} items on {len(plates)} plates")


if __name__ == "__main__":
    main()
