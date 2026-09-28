#!/usr/bin/env bash
set -euo pipefail

desktop_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
app="$desktop_root/src-tauri/target/release/bundle/macos/Manga Desk.app"
version="$(node -e 'console.log(require(process.argv[1]).version)' "$desktop_root/package.json")"
arch="$(uname -m)"
output_dir="${1:-$desktop_root/release-build-macos}"
output_dir="$(mkdir -p "$output_dir" && cd "$output_dir" && pwd)"
dmg="$output_dir/Manga.Desk_${version}_macos_${arch}.dmg"

if [[ ! -d "$app" ]]; then
  echo "Missing macOS app bundle: $app" >&2
  exit 1
fi

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
ditto "$app" "$stage/Manga Desk.app"
ln -s /Applications "$stage/Applications"
hdiutil create -quiet -volname "Manga Desk" -srcfolder "$stage" -format UDZO -ov "$dmg"
hdiutil verify -quiet "$dmg"
echo "Created $dmg"
