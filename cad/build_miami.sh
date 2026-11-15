#!/usr/bin/env bash
# Rebuild every Miami print file: full-colour STLs, 3MFs (regular + Bambu) for the
# plaque and the hanging sign, and the two-plate split project for the hanging sign.
# Run from anywhere; takes a while.
set -e
cd "$(dirname "$0")"
C="black yellow orange pink red white"
CC=$(echo $C | tr ' ' ,),miami@black     # the Miami lettering: its own part, black filament
mkdir -p stl/miami_plaque stl/miami_hanging stl/split/miami_hanging 3mf/bambu
rm -f stl/split/miami_hanging/*.stl

{
  for c in $C miami; do echo "miami_plaque.scad stl/miami_plaque/miami_plaque_$c.stl full all $c"; done
  for c in $C miami; do echo "miami_hanging.scad stl/miami_hanging/miami_hanging_$c.stl full all $c"; done
  for h in front back; do
    for c in $C miami; do echo "miami_hanging.scad stl/split/miami_hanging/${h}_sign_$c.stl $h sign $c"; done
    for c in black yellow; do echo "miami_hanging.scad stl/split/miami_hanging/${h}_stick_$c.stl $h stick $c"; done
  done
  echo "miami_hanging.scad stl/split/miami_hanging/front_keys_black.stl full keys black"
} | xargs -P "$(nproc)" -L 1 sh -c \
  'openscad -D "half=\"$2\"" -D "piece=\"$3\"" -D "part=\"$4\"" -o "$1" "$0" >/dev/null 2>&1 || echo "  (nothing for $1)"'

for m in plaque hanging; do
  files="$(for c in $C; do echo $c=stl/miami_$m/miami_${m}_$c.stl; done) miami@black=stl/miami_$m/miami_${m}_miami.stl"
  python3 make_3mf.py 3mf/miami_$m.3mf "Golden Wolves - Miami $m" $files
  python3 make_3mf.py --bambu 3mf/bambu/miami_${m}_bambu.3mf "Golden Wolves - Miami $m" $files
done
python3 make_plates.py 3mf/bambu/miami_hanging_split_2plates.3mf "Golden Wolves - Miami hanging" $CC stl/split/miami_hanging
