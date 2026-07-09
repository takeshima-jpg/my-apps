#!/usr/bin/env bash
#
# pre-commit フックを .git/hooks にインストールする。
#   bash tools/install-hooks.sh
#
set -eu

ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT/tools/pre-commit"
DST="$ROOT/.git/hooks/pre-commit"

if [ ! -f "$SRC" ]; then
  echo "✗ $SRC が見つかりません。"
  exit 1
fi

cp "$SRC" "$DST"
chmod +x "$DST"
echo "✅ pre-commit を $DST にインストールしました。"
echo "   以後、*/index.html をコミットする際に自動で構文・規約チェックが走ります。"
