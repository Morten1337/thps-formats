#!/usr/bin/env bash
set -euo pipefail

# Build asscopy using uv + pyinstaller
EXAMPLE_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

printf "====================================================================\n"
printf "[building] %s...\n" "asscopy"
printf "====================================================================\n"

pushd "${EXAMPLE_PATH}/../.." >/dev/null
uv run --with pyinstaller \
  pyinstaller --onefile --clean --noconfirm \
  --paths . \
  --icon="${EXAMPLE_PATH}/asscopy.ico" \
  --name=asscopy \
  --distpath="${EXAMPLE_PATH}/dist" \
  --workpath="${EXAMPLE_PATH}/build" \
  --specpath="${EXAMPLE_PATH}" \
  "${EXAMPLE_PATH}/asscopy.py"
popd >/dev/null

printf '%s\n' "Build complete: ${EXAMPLE_PATH}/dist/"
ls -l "${EXAMPLE_PATH}/dist" || true
