# tools — my-apps 保守スクリプト

3点セット。いずれも日本語出力・実行例はリポジトリ直下からの相対パス。

| ツール | 役割 | 依存 |
|--------|------|------|
| `check_backup_health.py` | 全OSバックアップJSONの健全性を9項目チェック | Python 3.10+（標準ライブラリのみ） |
| `pre-commit` + `install-hooks.sh` + `extract_scripts.js` | コミット前の構文・規約検証 | Node.js（+ JSX検証に esbuild） |
| `drive_cleanup.py` | Drive の aix-drafts 固定名ファイルの重複掃除 | Python 3.10+ + google API クライアント |

> **前提**: この環境では `python` が Windows ストアのスタブのみ（実体未導入）でした。
> Python製2ツールを使う前に、python.org から Python 3.10+ を入れて
> `python --version` が正しく表示されることを確認してください。Node.js は導入済み。

---

## 1. check_backup_health.py — データ健全性チェック

```
python tools/check_backup_health.py <myapps-all-backup-*.json のパス>
```

終了コード: 異常なし=0 / 警告あり=1。結果は日本語レポートで標準出力。

チェック項目（すべて過去の事故の再発検知）:

1. **鮮度** — `savedAt` が24時間以内か（古ければ同期停止の疑い）
2. **ヒトメモID衝突** — `hitomemo[].id` の重複（1件削除で複数人が消える前兆）
3. **ヒトメモ同名重複** — 名前を正規化（括弧注記・空白除去・NFKC・小文字化）して重複検出
4. **Shot滞留** — `status=todo` かつ `dueDate` が3日以上過去（同一Lectica実験の重複滞留は★で強調）
5. **Lectica鮮度** — `status=active` なのに直近14日のログが無い実験
6. **仕組みの空転** — `nextExperience` 設定済みなのに直近30日に「経験」ログが無い人物数。
   **socialUniverse で `isTop10=true` の人物に限定**（Top10外の過去設定はノイズなので数えない）。
   SU⇔ヒトメモの紐づけは `hitoId` 優先・名前フォールバック（SU本体の `reflectToHitomemo` と同方式）。
   紐づかなかったTop10人物は「対象外」として明示する
7. **1dayログ欠落** — `onedayLogs` の最新日付と今日の差が2日以上
8. **必須キー欠落** — バックアップの主要キーが null（収集漏れ検知）
9. **routineOS.holidays** — null（祝日がバックアップされていない）

---

## 2. pre-commit — コミット前検証フック

### インストール（1回だけ）

```
bash tools/install-hooks.sh
```

`.git/hooks/pre-commit` にコピーされ、以後 `*/index.html` をコミットするたびに自動で走る。

### 何を検証するか（ステージ済み内容に対して）

1. `<script>`（src属性なし・`type="text/babel"`以外）を連結して `node --check`
2. `type="text/babel"`（hitomemo の JSX）があれば esbuild で構文検証
3. `hitomemo/index.html`: `Date.now().toString()`（radix無し）の再混入を禁止（`genUid()` 必須）
4. `task-os/index.html`: `BUILD_VER` が当日日付か（**警告のみ**・ブロックしない）

1〜3 のいずれかが失敗するとコミットを中止し、原因を日本語で表示する。

### esbuild について

JSX 検証には esbuild が必要。未導入でも `npx --yes esbuild` に自動フォールバックする
（初回のみ自動取得）。常用するなら `npm i -g esbuild` を推奨。

### 補足

`extract_scripts.js` はフックが呼ぶ抽出ヘルパー（node製）。HTML から `<script>` を
取り出して一時ファイルに書き出すだけ。Python には依存しない。

---

## 3. drive_cleanup.py — Drive掃除・世代管理（夜間ジョブ）

aix-drafts フォルダ（ID: `1dEA4ZZJi5E97Dk_MRNwG6EbBlINlMO3U`）の固定名ファイルを
「最新1件だけ残し、古い同名はゴミ箱へ」自動整理する。

### 掃除ルール（厳守）

- **対象（最新1件だけ残す）**: `aix-tasks.json` / `aix_draft_latest.json` /
  `aix_review_weekly.json` / `aix_review_monthly.json` / `aix-hitomemo.json` /
  `myapps-all-backup.json`
- **絶対に触らない**: 日付つきスナップショット
  (`myapps-all-backup-YYYY-MM-DD.json` / `myapps-weekly-YYYY-Www.json` /
  `myapps-all-backup-YYYY-MM.json`)、および上記以外の名前のファイル
  （※ファイル名の**完全一致**でしか対象にしないため、日付つきは自動的に除外される）
- 削除は**ゴミ箱**（`trashed=true`）のみ。完全削除はしない（30日は復元可能）
- 実行ログを `tools/logs/drive_cleanup_YYYY-MM-DD.log` に残す

### 使い方

```
python tools/drive_cleanup.py --dry-run   # 削除せず対象を表示（導入初週はこれ）
python tools/drive_cleanup.py             # 実際にゴミ箱へ移動
```

### 初回セットアップ（Google Cloud で OAuth クライアント作成）

1. 依存を入れる:
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```
2. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを選択（無ければ作成）
3. 「APIとサービス」→「ライブラリ」で **Google Drive API** を有効化
4. 「APIとサービス」→「OAuth同意画面」を設定（User type: 外部/内部いずれか。テストユーザーに
   自分の Google アカウントを追加）
5. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」→ アプリの種類 **デスクトップ**
6. 作成した JSON をダウンロードし、`tools/credentials.json` として保存
7. 初回実行時にブラウザで認可 → `tools/token.json`（refresh_token 入り）が生成され、以後は無人実行

> `credentials.json` と `token.json` は**秘密情報**。`tools/.gitignore` で除外済み（コミットしない）。

### スケジュール（Windows タスクスケジューラ）

毎日 23:30 実行、PC がスリープ中なら次回起動時に実行する例:

1. 「タスク スケジューラ」を開く →「基本タスクの作成」
2. トリガー: 毎日 23:30
3. 操作:「プログラムの開始」
   - プログラム: `python`（またはフルパス `C:\...\python.exe`）
   - 引数: `tools\drive_cleanup.py`（初週は `tools\drive_cleanup.py --dry-run`）
   - 開始（作業フォルダ）: リポジトリ直下（例 `C:\Users\竹嶋寛人\Documents\my-appsメンテ`）
4. 作成後、タスクのプロパティで
   -「スケジュールされた時刻にタスクを開始できなかった場合、すぐにタスクを開始する」にチェック
   -「タスクを実行するためにスリープを解除する」は任意
5. 初週は `--dry-run` でログ（`tools/logs/`）を確認し、想定どおりなら引数から `--dry-run` を外して本実行に切替。
