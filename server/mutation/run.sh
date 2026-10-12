#!/usr/bin/env bash
# Runs Cosmic Ray on one file inside the tatou-mutation docker image.
#   usage (from server/):  mutation/run.sh <module> [results-subdir]
# It works on a copy of src/ and test/ so my real files never get mutated.
# Results end up in mutation/results/[<subdir>/]<module>.*
set -euo pipefail
MODULE="$1"
SUBDIR="${2:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$(dirname "$HERE")"
mkdir -p "$HERE/results/$SUBDIR"

MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$SERVER_DIR:/src:ro" \
  -v "$HERE/results/$SUBDIR:/out" \
  tatou-mutation bash -c "
    set -e
    cp -r /src/src /src/test /src/pyproject.toml /work/
    cd /work
    cp /src/mutation/configs/$MODULE.toml cr.toml
    cosmic-ray init cr.toml session.sqlite
    cosmic-ray --verbosity=WARNING baseline cr.toml
    cosmic-ray exec cr.toml session.sqlite
    cr-report session.sqlite --show-pending > /out/$MODULE.report.txt
    cr-html session.sqlite > /out/$MODULE.html
    cp session.sqlite /out/$MODULE.sqlite
  "
