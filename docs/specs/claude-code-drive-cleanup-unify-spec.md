> ✅ 実装済み 2026-07-12 ・ パート1=a541b5b(gdDedupeDrafts廃止) / パート2=手順書 docs/specs/drive-cleanup-運用.md ＋ CLAUDE.md追記。dry-runで対象40件を確認済み

# Claude Code 実装依頼書：Drive掃除を一本化（ブラウザ側廃止＋Python手動運用）

方針：Drive重複掃除の担い手を drive_cleanup.py（手動・週1）に一本化する。
Task OSのブラウザ側掃除（gdDedupeDrafts）は完全廃止し、403エラーを根絶する。

## パート1：ブラウザ側 gdDedupeDrafts の完全廃止（task-os/index.html）

- gdAutoSync から gdDedupeDrafts の呼び出しを削除する。
- gdDedupeDrafts 関数本体、および専用ヘルパー（trash処理でdedupe専用のもの）を削除する。
  - ただし gdFetch など他でも使う共通関数は残す（dedupe専用部分だけ削除）。
- これにより：
  - GDrive同期時に PATCH/trash（403の発生源）が呼ばれなくなる → 403ログが根絶
  - 同期は「Driveから読む→取り込み→バックアップ保存」だけになる（掃除はしない）
- 「同期エラー（再試行）」ボタンの表示条件を確認：dedupe廃止で、取り込み/保存が成功すれば
  同期成功扱いになること（dedupe由来のエラー表示がもう出ないこと）。
- 「重複draft掃除」ボタン（サイドバーにあれば）も撤去、または「Drive掃除はツールで（週1手動）」の
  無効表示に。UIに掃除ボタンが残って誤解を生まないようにする。

### 検証（パート1）
- node --check（pre-commit）
- GDrive同期実行：403ログが一切出ない。取り込み・brief・バックアップ保存は従来どおり成功。
- 「同期エラー（再試行）」が出ない（正常同期時）。

## パート2：drive_cleanup.py の手動運用手順書（docs/drive-cleanup-運用.md 新規作成）

タスクスケジューラ登録はしない（夜間PCがスリープで発火しないため）。**週1・手動**運用にする。

作成する手順書の内容：
1. 前提：tools/credentials.json 設置済み。初回実行時にブラウザ認可→token.json 生成。
2. 実行コマンド：
   - dry-run（消さずに対象確認）：`python tools/drive_cleanup.py --dry-run`
   - 本番（実際にゴミ箱へ）：`python tools/drive_cleanup.py`
3. 運用リズム：**日曜の週次レビューのついで**に週1回実行する。
   - Claude Codeに「Drive掃除して（dry-run→確認→本番）」と頼めば、dry-run結果を提示→承認後に本番実行。
4. 掃除ルール（再掲・drive_cleanup.py の仕様どおり）：
   - 対象：固定名ファイルの古い重複のみ（aix-tasks.json / aix_draft_latest.json /
     aix_review_weekly.json / aix_review_monthly.json / aix-hitomemo.json / myapps-all-backup.json）
     を最新1つだけ残す。
   - 絶対に触らない：日付つきスナップショット（*-YYYY-MM-DD.json / *-YYYY-Www.json / *-YYYY-MM.json）、
     上記以外の名前のファイル。
   - 削除はゴミ箱（trashed=true）。30日は復元可能。
   - 実行ログは tools/logs/ に残す。
5. drive_cleanup.py が既に --dry-run 対応・所有外ファイル(403)を握り潰す実装なら、そのまま。
   未対応なら、所有外ファイルはスキップして処理を止めない実装にする。

### CLAUDE.md 追記
「Drive重複掃除は drive_cleanup.py（週1・手動）に一本化。ブラウザ側の自動掃除は廃止済み。
掃除は日曜の週次レビュー時に dry-run→本番 で実行する。」

## コミット（分割可）
「task-os: ブラウザ側のGDrive重複掃除(gdDedupeDrafts)を完全廃止。403エラーの発生源を除去し、
Drive掃除は drive_cleanup.py(週1手動)に一本化」
「docs: drive_cleanup.py の手動運用手順書を追加・CLAUDE.md追記」

## 補足（所有者向け）
- 廃止後、Drive掃除は最低週1回は実行してください（溜まりすぎ防止）。忘れた週があっても、
  固定名ファイルの重複が少し増えるだけで実害はありません（次回まとめて掃除されます）。
- 初回だけ dry-run の結果を私（claude.ai）にも見せてもらえれば、対象が妥当か一緒に確認します。
