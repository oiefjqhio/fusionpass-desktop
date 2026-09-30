#!/usr/bin/env bash
# Publish a Fusion Pass desktop release from ONE successful "Build Desktop Release" run:
#   mode build-only, target all, fp_rev <N>. Every installer then comes from one commit and
#   reports <upstream version>-fp<N> (code review 2026-09-29, report 22 F3/F7).
#   GH_TOKEN=... fusionpass/publish-release.sh <run-id> <fp-rev>
# Tag: v<upstream version>-fp<rev>. Windows MSI, macOS DMGs, Linux DEB/RPM/AppImage. The installers are not
# code-signed (owner 2026-09-29), but every file gets <file>.sig: an Ed25519 signature over its SHA-256 made
# with the key below, which the in-app updater checks before installing (owner 2026-09-30, report 22 F1).
set -euo pipefail
RUN="${1:?run id}"; REV="${2:?fusion pass revision}"; REPO=oiefjqhio/fusionpass-desktop
KEY=/root/.fusionpass-desktop-update-ed25519.pem
PUB=$(openssl pkey -in "$KEY" -pubout -outform DER | base64 -w0)
grep -q "\"$PUB\"" "$(dirname "$0")/../composeApp/src/desktopMain/kotlin/com/nuvio/app/features/updater/AppUpdaterPlatform.desktop.kt" \
  || { echo "the app's FP_UPDATE_PUBLIC_KEY is not this key; refusing to sign"; exit 1; }
dir=$(mktemp -d); trap 'rm -rf "$dir"' EXIT
gh run download "$RUN" -R "$REPO" -D "$dir"
files=$(find "$dir" -type f \( -name 'FusionPass-Windows-*.msi' -o -name 'FusionPass-macOS-*.dmg' -o -name 'FusionPass-Linux-*.deb' -o -name 'FusionPass-Linux-*.rpm' -o -name 'FusionPass-Linux-*.AppImage' \))
[ -n "$files" ] || { echo "no installers in run $RUN"; exit 1; }
ver=$(basename "$(echo "$files" | grep '\.msi$' | head -1)" .msi | sed -E 's/^FusionPass-Windows-x64-//')
[[ "$ver" == *-fp"$REV" ]] || { echo "run $RUN built $ver, not -fp$REV: dispatch build-only with fp_rev=$REV and target=all"; exit 1; }
for os in Windows macOS Linux; do
  echo "$files" | grep -q "FusionPass-$os-" || { echo "run $RUN has no $os installer; build target=all so every OS comes from one commit"; exit 1; }
done
for f in $files; do
  [[ "$(basename "$f")" == *"-$ver."* ]] || { echo "$(basename "$f") is not version $ver"; exit 1; }
  openssl dgst -sha256 -binary "$f" > "$dir/digest"   # pkeyutl -rawin needs a file, not a pipe
  openssl pkeyutl -sign -inkey "$KEY" -rawin -in "$dir/digest" | base64 -w0 > "$f.sig"
  openssl pkeyutl -verify -pubin -inkey <(openssl pkey -in "$KEY" -pubout) -rawin -in "$dir/digest" -sigfile <(base64 -d "$f.sig") >/dev/null \
    || { echo "signature self-check failed for $f"; exit 1; }
done
sigs=$(for f in $files; do echo "$f.sig"; done)
sha=$(gh run view "$RUN" -R "$REPO" --json headSha -q .headSha)
gh release create "v$ver" $files $sigs -R "$REPO" --target "$sha" --prerelease \
  --title "Fusion Pass desktop $ver" \
  --notes "Fusion Pass for Windows, Mac and Linux, all built from $sha. Based on Nuvio Desktop (GPL-3.0); source in this repository. Each file has a .sig that the app checks before it installs an update."
