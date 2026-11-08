#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
destination="$root/src/penny/report/assets/fonts"
mkdir -p "$destination"
cd "$work"
for package in '@fontsource-variable/space-grotesk' '@fontsource-variable/inter' '@fontsource/ibm-plex-mono'; do
  archive="$(npm pack "$package" --silent)"
  mkdir extracted
  tar -xzf "$archive" -C extracted
  case "$package" in
    *space-grotesk) cp extracted/package/files/space-grotesk-latin-wght-normal.woff2 "$destination/"; label=space-grotesk ;;
    *inter) cp extracted/package/files/inter-latin-wght-normal.woff2 "$destination/"; label=inter ;;
    *ibm-plex-mono) cp extracted/package/files/ibm-plex-mono-latin-{400,500}-normal.woff2 "$destination/"; label=ibm-plex-mono ;;
  esac
  cp extracted/package/LICENSE "$destination/$label-OFL.txt"
  node -p "const p=require('./extracted/package/package.json');p.name+' '+p.version" >> "$destination/VERSIONS.txt"
  rm -rf extracted
done
echo "Vendored Latin WOFF2 fonts and OFL licenses into $destination"
