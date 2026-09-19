#!/usr/bin/env bash
# Zip the resource pack so it can be dropped straight into .minecraft/resourcepacks/.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pack="$root/nuit-eternal-sky"
out="${1:-$root/nuit-eternal-sky.zip}"

rm -f "$out"
# Zip from inside the pack: pack.mcmeta has to sit at the root of the archive.
(cd "$pack" && zip -rq "$out" pack.mcmeta pack.png assets)
printf 'wrote %s (%s)\n' "$out" "$(du -h "$out" | cut -f1)"
