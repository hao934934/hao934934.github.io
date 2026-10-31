#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
REPO_URL="${REPO_URL:-https://hao934934.github.io/}"; mkdir -p debs
command -v apt-ftparchive >/dev/null 2>&1 || { echo "缺少 apt-ftparchive"; exit 1; }
DEBS_ABS="$ROOT/debs"
if apt-ftparchive packages "$DEBS_ABS" >/dev/null 2>&1; then
  apt-ftparchive packages "$DEBS_ABS" | sed "s#^Filename: .*/#Filename: debs/#" > Packages
else
  SCAN="$(mktemp -d)/debs"; mkdir -p "$SCAN"; cp -f "$DEBS_ABS"/*.deb "$SCAN"/ 2>/dev/null || true
  apt-ftparchive packages "$SCAN" | sed "s#^Filename: .*/#Filename: debs/#" > Packages
fi
[ -f overrides.json ] && command -v python3 >/dev/null 2>&1 && python3 scripts/apply-overrides.py
gzip -9 -kf Packages
gen_hashes(){ local alg="$1"; shift; local f; for f in "$@"; do [ -f "$f" ] || continue;
  local size; size=$(wc -c < "$f" | tr -d ' '); local h;
  case "$alg" in md5) h=$(md5sum "$f"|awk '{print $1}');; sha256) h=$(sha256sum "$f"|awk '{print $1}');; esac
  printf ' %s  %s %s\n' "$h" "$size" "$f"; done; }
{ echo "Origin: hao934934 的源"; echo "Label: hao934934 的源"; echo "Suite: stable"; echo "Version: 1.0";
  echo "Codename: ios"; echo "Architectures: iphoneos-arm64 iphoneos-arm64e"; echo "Components: main";
  echo "Description: hao934934 的越狱软件源"; echo "Support: $REPO_URL";
  echo "MD5Sum:"; gen_hashes md5 Packages Packages.gz; echo "SHA256:"; gen_hashes sha256 Packages Packages.gz; } > Release
echo "索引完成: $(grep -c '^Package:' Packages) 个包"