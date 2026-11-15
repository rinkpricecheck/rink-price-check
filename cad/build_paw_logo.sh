#!/usr/bin/env bash
# Rebuild the Miami paw logo plaque: per-colour STLs and the 3MFs (regular + Bambu).
set -e
cd "$(dirname "$0")"
C="black yellow white red gray"
mkdir -p stl/miami_paw_logo 3mf/bambu
for c in $C; do echo "$c"; done | xargs -P "$(nproc)" -I{} \
  openscad -D 'part="{}"' -o stl/miami_paw_logo/miami_paw_logo_{}.stl miami_paw_logo.scad >/dev/null 2>&1
d=stl/miami_paw_logo/miami_paw_logo
files="black=${d}_black.stl yellow=${d}_yellow.stl white=${d}_white.stl red=${d}_red.stl claws@gray=${d}_gray.stl"
python3 make_3mf.py 3mf/miami_paw_logo.3mf "Golden Wolves - Miami paw logo" $files
python3 make_3mf.py --bambu 3mf/bambu/miami_paw_logo_bambu.3mf "Golden Wolves - Miami paw logo" $files
