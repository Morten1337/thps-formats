#!/usr/bin/env bash
set -euo pipefail

# Build fontgen using uv + pyinstaller
EXAMPLE_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

printf "====================================================================\n"
printf "[building] %s...\n" "fontgen"
printf "====================================================================\n"

pushd "${EXAMPLE_PATH}/../.." >/dev/null
uv run --with pyinstaller \
  pyinstaller --onefile --clean --noconfirm \
  --paths . \
  --hidden-import=PIL \
  --hidden-import=PIL._imaging \
  --hidden-import=PIL.Image \
  --icon="${EXAMPLE_PATH}/fontgen.ico" \
  --name=fontgen \
  --distpath="${EXAMPLE_PATH}/dist" \
  --workpath="${EXAMPLE_PATH}/build" \
  --specpath="${EXAMPLE_PATH}" \
  "${EXAMPLE_PATH}/fontgen.py"
popd >/dev/null

printf '%s\n' "Build complete: ${EXAMPLE_PATH}/dist/"
ls -l "${EXAMPLE_PATH}/dist" || true
