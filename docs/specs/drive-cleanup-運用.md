# Drive掃除 運用手順書（drive_cleanup.py・週1手動）

Drive上の「固定名ファイルの古い重複」を掃除する運用。ブラウザ側の自動掃除（Task OSのgdDedupeDrafts）は
廃止済みで、掃除は **この Python ツールに一本化**。タスクスケジューラは使わない（夜間PCスリープで発火しない
ため）。**日曜の週次レビューのついでに週1回・手動**で実行する。

## 前提

- `tools/credentials.json`（OAuthデスクトップクライアント）が設置済み。作成手順は `tools/README.md`。
- 初回実行時にブラウザ認可が走り、`tools/token.json`（refresh_token）が生成される。以降は自動更新。
- **⚠️ 認可アカウントは必ず `takeshima@3a-c.com`（ファイル所有者）で行う。** マイドライブのファイルは
  所有者しかゴミ箱に入れられない（編集者権限では trash が403になる）。誤って別アカウント（個人Gmail等）で
  認可すると、対象が全て403スキップされ0件しか掃除できない（2026-07-13 に実際に発生）。誤認可時は
  `tools/token.json` を退避 → `--dry-run` を再実行 → OAuth画面で `takeshima@3a-c.com` を選び直す。

### 🚧 現状（2026-07-20）：会社アカウントでの再認可は行き止まり — 自動掃除は当面保留
- この OAuthアプリ（Cloudプロジェクト `my-apps-498101`・クライアントID `450582924828-…apps.googleusercontent.com`・
  User type=外部/本番・未確認）は、`drive` が**制限付きスコープ**のため、`takeshima@3a-c.com`（`3a-c.com` Workspace）で
  認可しようとすると管理ポリシーに**「このアプリはブロックされます」**と拒否される。個人Gmailは所有者でないので掃除不可。
- 正攻法は `3a-c.com` の **Workspace 管理者**が Admin Console（セキュリティ→API制御→サードパーティアプリ）で
  上記クライアントIDを**「信頼済み」**に登録すること。**所有者は当該Workspaceの管理者ではない**ため、これは実施不可。
- 別解（自動化を復活させたい場合のみ）：`takeshima@3a-c.com` 側で新規Cloudプロジェクトを作り、
  OAuth同意画面の **User type を「内部(Internal)」** にすれば未確認でもドメイン内利用は許可される
  （＝ブロックされない・本番モードならトークンも長命）。ただし会社アカウントでのプロジェクト作成権限が要る。
- **結論：無理に自動化を追わない。** 重複42件は「固定名ファイルの古い版が残るだけ」で動作に無害。
  どうしても消したい時は、`takeshima@3a-c.com` でログインした Drive の Web UI から、固定名ごとに
  最新1つを残して古い版を手動でゴミ箱へ（各名で modifiedTime 降順に並べ替え）。本ツールでの自動掃除は保留。
- Python 実行パス：`C:\Users\竹嶋寛人\AppData\Local\Programs\Python\Python312\python.exe`
  （`python` 単体はストアのスタブなので使わない）。
- 依存：google-api-python-client / google-auth / google-auth-oauthlib（未導入なら pip install）。

## 実行コマンド

```
# dry-run（消さずに対象を表示。まずこれで確認）
python tools/drive_cleanup.py --dry-run

# 本番（実際にゴミ箱へ移動）
python tools/drive_cleanup.py
```

## 運用リズム

- **日曜の週次レビューのついで**に週1回。忘れた週があっても、固定名ファイルの重複が少し増えるだけで実害なし
  （次回まとめて掃除される）。
- Claude Code に「Drive掃除して（dry-run→確認→本番）」と頼めば、**dry-run結果を提示 → 承認後に本番実行**する。

## 掃除ルール（drive_cleanup.py の仕様）

- **対象**：aix-drafts フォルダ内の次の固定名ファイルの古い重複のみ。各名前で**最新1つだけ残す**。
  - `aix-tasks.json` / `aix_draft_latest.json` / `aix_review_weekly.json` /
    `aix_review_monthly.json` / `aix-hitomemo.json`
  - ※`myapps-all-backup.json` は 2026-07-26 Drive再編でバックアップを 90_バックアップ へ移したため対象から除外
    （直下前提が崩れたため。週次スナップショットの整理は Task OS 側が 90 で行う）
- **絶対に触らない**：
  - 日付つきスナップショット（`*-YYYY-MM-DD.json` / `*-YYYY-Www.json` / `*-YYYY-MM.json`）。
    ※週次スナップショット（myapps-weekly-*）の保持は Task OS 側の gdPruneWeekly が担当（直近8週）。本ツールは触らない。
  - 上記の固定名リスト以外の名前のファイル。
- **削除はゴミ箱**（trashed=true）。30日は復元可能。完全削除はしない。
- **所有外ファイル（trash 403）はスキップして続行**（このOAuthアプリの所有でない＝Drive Desktop同期等で
  作られたファイルは trash できない。per-file の except で握り潰し、処理は止めない）。
- 実行ログは `tools/logs/drive_cleanup_YYYY-MM-DD.log` に残る。

## 補足

- 初回だけ dry-run の結果を claude.ai にも見せると、対象が妥当か一緒に確認できる。
- 本ツールは日付/週タグ付きスナップショットには触れないため、誤って復元用バックアップを消す心配はない。
