#!/usr/bin/env bash
set -euo pipefail

# Build runmenow using uv + pyinstaller
# Note: runmenow is Windows-only (uses pywin32 and --noconsole); skip on other OSes.
EXAMPLE_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

OS_NAME="$(uname -s | tr '[:upper:]' '[:lower:]')"
if [[ "${OS_NAME}" != *mingw* && "${OS_NAME}" != *msys* && "${OS_NAME}" != *cygwin* && "${OS_NAME}" != *windows* ]]; then
  printf '%s\n' "runmenow build is Windows-only; skipping on ${OS_NAME}."
  exit 0
fi

printf "====================================================================\n"
printf "[building] %s...\n" "runmenow"
printf "====================================================================\n"

pushd "${EXAMPLE_PATH}/../.." >/dev/null
uv run --with pyinstaller --with pywin32 \
  pyinstaller --onefile --clean --noconfirm \
  --paths . \
  --noconsole \
  --icon="${EXAMPLE_PATH}/runmenow.ico" \
  --name=runmenow \
  --distpath="${EXAMPLE_PATH}/dist" \
  --workpath="${EXAMPLE_PATH}/build" \
  --specpath="${EXAMPLE_PATH}" \
  "${EXAMPLE_PATH}/runmenow.py"
popd >/dev/null

printf '%s\n' "Build complete: ${EXAMPLE_PATH}/dist/"
ls -l "${EXAMPLE_PATH}/dist" || true
