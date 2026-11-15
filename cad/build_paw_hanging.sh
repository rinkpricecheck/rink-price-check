#!/usr/bin/env bash
# Rebuild the hanging Miami paw logo sign: front/back halves per colour, the keys,
# and the two-plate Bambu project (laid out for the H2C bed).
set -e
cd "$(dirname "$0")"
D=stl/split/miami_paw_hanging
mkdir -p $D 3mf/bambu
rm -f $D/*.stl
{
  for h in front back; do
    for c in black yellow white red; do echo "$D/${h}_sign_$c.stl $h sign $c"; done
    echo "$D/${h}_sign_claws.stl $h sign gray"
  done
  echo "$D/front_keys_black.stl full keys black"
} | xargs -P "$(nproc)" -L 1 sh -c \
  'openscad -D "half=\"$1\"" -D "piece=\"$2\"" -D "part=\"$3\"" -o "$0" miami_paw_hanging.scad >/dev/null 2>&1 || echo "  (nothing for $0)"'
BED=350 python3 make_plates.py 3mf/bambu/miami_paw_hanging_split_2plates.3mf "Golden Wolves - Miami paw hanging" \
  black,yellow,white,red,claws@gray $D
