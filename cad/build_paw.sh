#!/usr/bin/env bash
# Rebuild the Miami paw plaque: per-colour STLs and the 3MFs (regular + Bambu).
set -e
cd "$(dirname "$0")"
C="black yellow red white"
mkdir -p stl/miami_paw 3mf/bambu
for c in $C miami; do echo "$c"; done | xargs -P "$(nproc)" -I{} \
  openscad -D 'part="{}"' -o stl/miami_paw/miami_paw_{}.stl miami_paw.scad >/dev/null 2>&1
files="$(for c in $C; do echo $c=stl/miami_paw/miami_paw_$c.stl; done) miami@red=stl/miami_paw/miami_paw_miami.stl"
python3 make_3mf.py 3mf/miami_paw.3mf "Golden Wolves - Miami paw" $files
python3 make_3mf.py --bambu 3mf/bambu/miami_paw_bambu.3mf "Golden Wolves - Miami paw" $files
