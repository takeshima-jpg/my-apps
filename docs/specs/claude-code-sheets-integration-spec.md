# Claude Code 実装依頼書：スプレッドシート連携（Project OS直接取り込み ＋ シート更新ツール）

目的：プロジェクト更新の工数を「シート更新（手動 or Claude Code）→ Project OSでボタン1回」まで減らす。
**既存の貼り付け取り込み（コピペ→解析）は一切変更せず残す**（細かい更新はシート側で直接行い、貼り付けでも取り込めるようにするため）。

---

## Part 0：GCP設定（1回だけ・所有者と一緒に）

drive_cleanup.py 用のOAuthクライアントと**共用**する。
1. Google Cloud Console：既存プロジェクトで **Google Sheets API を有効化**（Drive APIも未了なら有効化）
2. OAuthクライアント（デスクトップ）= drive_cleanup と同じ credentials.json を使用
3. スコープ：`https://www.googleapis.com/auth/drive` ＋ `https://www.googleapis.com/auth/spreadsheets`
4. 初回実行時にブラウザ認可 → token.json 保存（以後無人）
5. **Part A（ブラウザ側）は別**：project-os の Web OAuth は既存OSと同じ CLIENT_ID を使い、
   Google Cloud Console の承認済みリダイレクトURIに `https://takeshima-jpg.github.io/my-apps/project-os/index.html` を追加。
   Sheets APIの有効化は 1 と共通。

---

## Part A：Project OS「⟳ シートから取り込み」ボタン

### 仕様
- 各プロジェクト画面の既存「シートを取り込む（貼り付け）」の**隣**にボタンを追加：「⟳ シートから直接取り込み」
- 動作：
  1. プロジェクトの sheetUrl から spreadsheetId と gid を抽出（gid無しは最初のシート）
  2. Sheets API v4 で読み取り：metadata（spreadsheets.get）で gid→シート名を解決 → values.get で `A:K`（11列：ID/テーマ/種別/期日/状態/イベント/担当/対象/施策/ゴール/結果）
  3. 取得した行列を、**既存の貼り付けパーサが受け取るのと同じテキスト（タブ区切り）に変換し、既存のパース→doImport処理をそのまま呼ぶ**（パーサの複製・改変は禁止。1本のパーサを共有する）
  4. 既存と同じ確認ダイアログ（全上書き警告）→ 適用 → 取り込み件数を既存と同じ形式で報告
- 認証：他OSのGDrive実装パターンを踏襲（CLAUDE.mdのGDrive共通注意を必読）。
  - スコープ：`https://www.googleapis.com/auth/spreadsheets.readonly`
  - トークンキー：`gdrive_token_projectos`（新規・他OSと衝突させない）
  - 未接続時はボタン押下でログイン誘導。トークン失効（401）は再接続を促す
- エラー時（シート非公開・URL不正・列不足）は日本語で原因を表示し、**貼り付け取り込みへ誘導**する
- 変更対象：project-os/index.html のみ。**貼り付け取り込みの経路・パーサ・確認ダイアログは無改変**

### 検証
- node --check（pre-commit）
- パーサ共有の確認：直接取り込みと貼り付け取り込みで同一シート内容→同一結果になることを、テスト行（イベント/分岐/制約×完了/未着手を含む）で確認
- 先日修正した「完了分岐→past」の挙動が直接取り込みでも効くこと

---

## Part B：tools/sheet_update.py ＋ シート更新の手順書

### 位置づけ
竹嶋さんが「JSS承継のシートを更新して：ID15を完了に、8月末に父面談の行を追加」のように言ったら、
Claude Codeがこのツールでシートを直接更新する。**書き込み前に必ず差分を提示して承認を得る**。

### シート台帳：docs/sheets.md（新規作成）
```
| プロジェクト名 | spreadsheetId | シート名/gid | 備考 |
| JSS承継親孝行 | （所有者に確認して記入） | | 11列・ID=テーマ番号×10+連番 |
| 3AHD2030構想 | | | |
```
初回に所有者へURLを確認して埋める。以後「◯◯のシート」で通じるようにする。

### tools/sheet_update.py の機能
```
python tools/sheet_update.py <spreadsheetId> --get                    # 現状をTSVで表示
python tools/sheet_update.py <spreadsheetId> --set-status <ID> 完了   # 状態列の更新
python tools/sheet_update.py <spreadsheetId> --append-tsv <file>      # 行追加（TSV）
python tools/sheet_update.py <spreadsheetId> --backup                 # 全値をtools/logs/へ退避
```
- ただし実運用はコマンド直叩きではなく、**Claude Codeが自然言語の依頼を解釈**して --get → 変更案の差分提示 → 承認後に書き込み、の流れで使う

### 書き込みルール【厳守】
1. **書き込み前に必ず**：現状を --backup で退避 → 変更差分（何行のどの列がどう変わるか）をチャットに提示 → 所有者の「OK」を待つ
2. 行削除はしない（状態を変える・行を足すのみ。削除は所有者がシートで直接行う）
3. 列構成（11列）と日付形式（シートの既存表記に合わせる）を崩さない
4. 新規行のIDは、シートの採番規則（テーマ番号×10＋連番。例：テーマ2なら 21,22,…）を読み取って次番を振る。規則が読み取れなければ所有者に1問確認
5. 書き込み後、--get で結果を再取得して反映を確認し、「シート更新完了。Project OSで『⟳ シートから直接取り込み』を押してください」と報告

### CLAUDE.md への追記（1行）
「シート更新は docs/claude-code-sheets-integration-spec.md の手順に従う（書き込み前バックアップ＋差分承認必須）」

---

## 完了条件
- 貼り付け取り込みが従来どおり動く（無改変）
- 直接取り込みボタンで同一結果が得られる
- sheet_update.py で状態変更・行追加ができ、バックアップと差分承認のフローが機能する
- 新しい運用：シート直接編集 or Claude Codeに依頼 → Project OSでボタン1回（コピペ不要）
