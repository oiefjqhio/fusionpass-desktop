#!/usr/bin/env bash
# Publish a Fusion Pass desktop release from a successful "Build Desktop Release" build-only run.
#   GH_TOKEN=... fusionpass/publish-release.sh <run-id> <fp-rev>
# Tag: v<upstream version>-fp<rev>. Windows MSI + macOS DMGs.
set -euo pipefail
RUN="${1:?run id}"; REV="${2:?fusion pass revision}"; REPO=oiefjqhio/fusionpass-desktop
dir=$(mktemp -d); trap 'rm -rf "$dir"' EXIT
gh run download "$RUN" -R "$REPO" -D "$dir"
files=$(find "$dir" -type f \( -name 'FusionPass-Windows-*.msi' -o -name 'FusionPass-macOS-*.dmg' \))
[ -n "$files" ] || { echo "no installers in run $RUN"; exit 1; }
ver=$(basename "$(echo "$files" | grep '\.msi$' | head -1)" .msi | sed -E 's/^FusionPass-Windows-x64-//')
sha=$(gh run view "$RUN" -R "$REPO" --json headSha -q .headSha)
gh release create "v$ver-fp$REV" $files -R "$REPO" --target "$sha" --prerelease \
  --title "Fusion Pass desktop $ver-fp$REV" \
  --notes "Fusion Pass for Windows and Mac. Based on Nuvio Desktop (GPL-3.0); source in this repository."
