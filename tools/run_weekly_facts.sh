#!/usr/bin/env bash
#
# 日曜の週次レビュー用ワンコマンド
#   1. 最新の myapps-all-backup*.json を自動で見つける
#      （Downloads の日付付き ＋ Cowork作業フォルダの固定名 myapps-all-backup.json を対象に、更新時刻が最新のもの）
#   2. tools/weekly_facts.py に食わせ、--prev 付きで実行（前週サマリも出す）
#   3. 出力された weekly-facts.json を Coworkの作業フォルダ（GDrive aix-drafts/20_週次・月次）に置く
#
# 使い方:
#   bash tools/run_weekly_facts.sh              # 対象週 = 今日を含む週（月曜起点）
#   bash tools/run_weekly_facts.sh 2026-07-06   # 指定日を含む週を対象にする
#
# Git Bash（Windows）前提。バックアップの鮮度チェック付き（24時間より古ければ警告）。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COWORK_DIR="/g/マイドライブ/aix-drafts"   # Coworkが読む作業フォルダ（Google Drive同期）
DL_DIR="$HOME/Downloads"

# Python 実体（PATH上の python はストアのスタブなので使わない）
PY="$(cygpath -u "$LOCALAPPDATA")/Programs/Python/Python312/python.exe"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || command -v python)" || {
    echo "✗ Python が見つかりません"; exit 1; }
fi

if [ ! -d "$COWORK_DIR" ]; then
  echo "✗ Cowork作業フォルダが見つかりません: $COWORK_DIR"
  echo "  Google Drive デスクトップが起動しているか確認してください。"
  exit 1
fi

# ── 1. 最新バックアップを拾う（固定名ではなく更新時刻で選ぶ）──
LATEST="$(ls -t "$DL_DIR"/myapps-all-backup*.json "$COWORK_DIR"/myapps-all-backup*.json 2>/dev/null | head -1 || true)"
if [ -z "$LATEST" ]; then
  echo "✗ myapps-all-backup*.json が見つかりません（Downloads / $COWORK_DIR を確認）"
  echo "  Task OS で統合バックアップを出してから再実行してください。"
  exit 1
fi

# 鮮度チェック: 24時間より古いバックアップなら警告（処理は続行）
AGE_H=$(( ( $(date +%s) - $(stat -c %Y "$LATEST") ) / 3600 ))
echo "入力バックアップ: $LATEST（${AGE_H}時間前）"
if [ "$AGE_H" -ge 24 ]; then
  echo "⚠ バックアップが24時間以上前です。今日の分を Task OS から出し直すことを推奨します。"
fi

# ── 2. weekly_facts.py を --prev 付きで実行 ──
#     （weekly-facts.json は入力バックアップと同じフォルダに出る）
ANCHOR="${1:-}"
PYTHONUTF8=1 "$PY" "$ROOT/tools/weekly_facts.py" "$LATEST" ${ANCHOR:+"$ANCHOR"} --prev

# ── 3. 出力を Cowork作業フォルダへ ──
#     2026-07-26 Drive再編：aix-drafts直下ではなく 20_週次・月次 サブフォルダに置く（なければ作る）
OUT="$(dirname "$LATEST")/weekly-facts.json"
DEST_DIR="$COWORK_DIR/20_週次・月次"
DEST="$DEST_DIR/weekly-facts.json"
mkdir -p "$DEST_DIR"
if [ "$(cd "$(dirname "$OUT")" && pwd)" != "$(cd "$DEST_DIR" && pwd)" ]; then
  cp "$OUT" "$DEST"
fi
echo ""
echo "✅ $DEST に配置しました。Coworkの週次レビューでこのファイルを読ませてください。"
