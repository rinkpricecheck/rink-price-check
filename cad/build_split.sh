#!/usr/bin/env bash
# Export the split (front/back) print parts for both hanging signs and build
# the two-plate Bambu projects.  Run from the cad/ folder.  Takes a while.
set -e
cd "$(dirname "$0")"

BAUER_C="black yellow cream red white"
MIAMI_C="black yellow orange pink red white"
mkdir -p stl/split/bauer stl/split/miami_hanging 3mf/bambu

jobs_list=()
for h in front back; do
  for c in $BAUER_C; do jobs_list+=("rink_sign.scad stl/split/bauer $h sign $c"); done
  for c in black yellow; do jobs_list+=("rink_sign.scad stl/split/bauer $h stick $c"); done
  for c in $MIAMI_C; do jobs_list+=("miami_hanging.scad stl/split/miami_hanging $h sign $c"); done
  for c in black yellow; do jobs_list+=("miami_hanging.scad stl/split/miami_hanging $h stick $c"); done
done

printf '%s\n' "${jobs_list[@]}" | xargs -P "$(nproc)" -L 1 sh -c \
  'openscad -D "half=\"$2\"" -D "piece=\"$3\"" -D "part=\"$4\"" -o "$1/$2_$3_$4.stl" "$0" >/dev/null 2>&1 || echo "  (no $4 in $2 $3)"'

python3 make_plates.py 3mf/bambu/rink_sign_bauer_split_2plates.3mf "305 Golden Wolves - Bauer" \
  "$(echo $BAUER_C | tr ' ' ,)" stl/split/bauer
python3 make_plates.py 3mf/bambu/miami_hanging_split_2plates.3mf "305 Golden Wolves - Miami hanging" \
  "$(echo $MIAMI_C | tr ' ' ,)" stl/split/miami_hanging
