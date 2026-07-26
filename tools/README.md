# tools — my-apps 保守スクリプト

保守スクリプト群。いずれも日本語出力・実行例はリポジトリ直下からの相対パス。

| ツール | 役割 | 依存 |
|--------|------|------|
| `check_backup_health.py` | 全OSバックアップJSONの健全性を11項目チェック | Python 3.10+（標準ライブラリのみ） |
| `weekly_facts.py` + `run_weekly_facts.sh` | 週次レビュー用「今週の完了・実行」を機械計算（日曜ワンコマンド） | Python 3.10+（標準ライブラリのみ） |
| `pre-commit` + `install-hooks.sh` + `extract_scripts.js` | コミット前の構文・規約検証 | Node.js（+ JSX検証に esbuild） |
| `drive_cleanup.py` | Drive の aix-drafts 固定名ファイルの重複掃除 | Python 3.10+ + google API クライアント |
| `sheet_update.py` | Project OS シートの状態変更・行追加（書込前バックアップ＋差分承認） | Python 3.10+ + google API クライアント |

> **前提**: PATH上の `python` は Windows ストアのスタブなので使わない。実体は
> `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`（2026-07-09 にwingetで導入）。
> Windowsコンソールで日本語が化ける場合は `$env:PYTHONUTF8=1` を付ける。Node.js は導入済み。

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
10. **Reflect本体** — `reflectOS_idb` の存在と中身（reflect-os未移行のブラウザでバックアップすると空になる）
11. **巻き戻り検知** — 前回実行時の各OSの「最新エントリ日付」「件数」を `tools/logs/health_state.json` に
    保存し、減っていたら⚠（2026-07 1day巻き戻り事故の再発検知）。基準の更新は検査対象の `savedAt` が
    基準より新しいときだけ（古いバックアップの検査で基準を壊さない）。Reflectログは日次スナップショットで
    直近60日に間引かれるため件数比較をせず最新日付のみ比較

---

## 2. weekly_facts.py — 週次「今週の完了・実行」の機械計算

週次レビューの数字を、Coworkの推測ではなく**completedAt／実行日ベースの機械計算**で確定する。
「却下(rejected)」「破棄(discarded)」「データから消えただけ」は完了に混ぜない。

完了・実行の判定（**検証済み・変更しないこと**）:

- **Shot** = `status=='done'` かつ `completedAt` が週内
- **100LIST** = `completed==True` かつ `discarded` でない かつ `completedAt` が週内
- **Routine** = `logs` の `actionDate` が週内（1ログ=1実行）
- **Lectica** = `lecticaLogs` の `date` が週内
- **1day** = `onedayLogs` の `date` が週内（archived除外・満足度/フラグ分布付き）
- **Project** = `updatedAt` が週内（「完了」ではなく「動きのあったPJ」。解釈はCowork側）

```
python tools/weekly_facts.py <backup.json>                  # 対象週 = 今日を含む週（月曜起点）
python tools/weekly_facts.py <backup.json> 2026-07-06        # 指定日を含む週
python tools/weekly_facts.py <backup.json> 2026-07-06 --prev # 前週も併せて出力（再掲禁止判定用）
```

`weekly-facts.json` を**入力バックアップと同じフォルダ**に出力し、標準出力にカウントサマリを表示する。

### 日曜の運用（3ステップ）

1. Task OS で統合バックアップ（myapps-all-backup）を出す
2. `bash tools/run_weekly_facts.sh` を実行（最新バックアップを自動で拾い `--prev` 付きで計算）
3. `G:\マイドライブ\aix-drafts\20_週次・月次` に置かれた `weekly-facts.json` をCoworkの週次レビューに渡す（2026-07-26 Drive再編でサブフォルダ化）

`run_weekly_facts.sh` は Downloads の日付付きバックアップと aix-drafts の固定名バックアップから
**更新時刻が最新のもの**を選ぶ（ファイル名は日付で変わるため固定名参照はしない）。
24時間より古いバックアップしか無い場合は警告を出す。

> 旧版（2スナップショット差分方式・`aix_weekly_facts.json` 出力・2026-07-10 `4cfc2f6`）は
> `tools/archive/` に退避（テストごと）。2026-07-17 に単一バックアップ＋週窓方式の本版へ差し替えた。

---

## 3. pre-commit — コミット前検証フック

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

## 4. drive_cleanup.py — Drive掃除・世代管理（夜間ジョブ）

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
3. 「APIとサービス」→「ライブラリ」で **Google Drive API** と **Google Sheets API** を有効化
   （Sheets API は `sheet_update.py` と同じ token.json を共用するため）
4. 「APIとサービス」→「OAuth同意画面」を設定（User type: 外部/内部いずれか。テストユーザーに
   自分の Google アカウントを追加）
5. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」→ アプリの種類 **デスクトップ**
6. 作成した JSON をダウンロードし、`tools/credentials.json` として保存
7. 初回実行時にブラウザで認可 → `tools/token.json`（refresh_token 入り）が生成され、以後は無人実行

> `credentials.json` と `token.json` は**秘密情報**。ルート `.gitignore` で除外済み（コミットしない）。
> スコープは `drive` ＋ `spreadsheets` の和集合。`drive_cleanup.py` と `sheet_update.py` が
> 同じ `credentials.json` / `token.json` を共用する（どちらで初回認可しても両方使える）。

> **⚠️ 認可アカウントは `takeshima@3a-c.com`（ブラウザ側アプリの書き込み主体＝ファイル所有者）で行う。**
> Driveの仕様上、マイドライブのファイルは**所有者本人しかゴミ箱に入れられない**（編集者権限では403）。
> 2026-07-13、token.json が誤って個人Gmail `h.takeshima727@gmail.com`（フォルダの編集者だが非所有者）で
> 認可されていたため、本番実行で対象42件が全て403スキップ＝0件しか掃除できない事故が起きた。
> 再認可時は OAuth 画面で**必ず `takeshima@3a-c.com` を選ぶ**こと。誤アカウントの token を作ってしまったら
> `tools/token.json` を削除（退避）してから `--dry-run` を実行し、正しいアカウントで認可し直す。

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

---

## 5. sheet_update.py — Project OS シートの状態変更・行追加

竹嶋さんが「◯◯のシートを更新して：ID15を完了に、8月末に父面談の行を追加」のように言ったら、
Claude Code がこのツールでシートを直接更新する。認証は `drive_cleanup.py` と共用（上記セットアップ済みが前提）。

```
python tools/sheet_update.py <spreadsheetId> --get                 # 現状をTSVで表示
python tools/sheet_update.py <spreadsheetId> --set-status <ID> 完了 # 状態列を更新
python tools/sheet_update.py <spreadsheetId> --append-tsv <file>    # 行追加（TSV）
python tools/sheet_update.py <spreadsheetId> --backup               # 全値をtools/logs/へ退避
（対象タブは既定で先頭シート。 --gid <n> / --sheet-name <名> で指定可）
```

### 運用（Claude Code が自然言語の依頼を解釈して実行）

`docs/specs/claude-code-sheets-integration-spec.md` と `docs/sheets.md` に従う。**書き込み前バックアップ＋差分承認が必須**：

1. `--get` で現状取得 → 変更差分（何行のどの列がどう変わるか）をチャットに提示 → 所有者の「OK」を待つ
2. 承認後に `--set-status` / `--append-tsv`（書き込み系は実行前に自動で `tools/logs/` へバックアップ）
3. `--get` で反映を確認し、「Project OS で『⟳ シートから直接取り込み』を押してください」と報告
4. 行削除はしない（状態変更・行追加のみ）。11列構成・日付形式・ID採番規則（テーマ番号×10＋連番）を崩さない

シート台帳（プロジェクト名⇔spreadsheetId）は `docs/sheets.md`（雛形・公開）／`docs/sheets.local.md`（実データ・非公開）。

### テスト

```
python tools/test_sheet_update.py   # 純粋ヘルパー7件（ヘッダー検出/列特定/A1変換など・API非依存）
```
