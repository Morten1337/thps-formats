#!/usr/bin/env bash
set -euo pipefail

EXAMPLES_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

failed=()

printf "====================================================================\n"
printf "[building] example tools\n"
printf "====================================================================\n"

"${EXAMPLES_DIR}/qcompy/build.sh"   || failed+=("qcompy")
"${EXAMPLES_DIR}/prepack/build.sh"  || failed+=("prepack")
"${EXAMPLES_DIR}/fontgen/build.sh"  || failed+=("fontgen")
"${EXAMPLES_DIR}/asscopy/build.sh"  || failed+=("asscopy")
"${EXAMPLES_DIR}/runmenow/build.sh" || failed+=("runmenow")

printf "\n"
printf "====================================================================\n"
printf "build summary\n"
printf "====================================================================\n"

if ((${#failed[@]} > 0)); then
  printf "failed builds: %s\n" "${failed[*]}"
  exit 1
else
  printf "all builds completed successfully!\n"
fi
