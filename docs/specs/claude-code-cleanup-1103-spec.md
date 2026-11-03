# Claude Code 実装依頼書：使っていない欄・古い写しの片付けと、SU の見直し記録をバックアップへ

作成日：2026-11-03（メンテナンス担当。本人決定 11/3：5・6・7 とも A）
対象：`project-os`、`reflect-os`、`launcher`、`hitomemo`、`task-os`、（必要なら）`social-universe`
土台：main `78dd181`。作業前に `git pull`。

---

## 1. Project OS の「Reflect の問い（問いのID）」欄を外す（決定5）

- `reflectQuestionId` は 11/3 時点で6PJとも0件。PJ と Reflect の問いのつながりは紐づけ行の「問い：」（`links.questionId`）で持つ
- 編集モーダルの欄（2738行付近）、保存（2754行付近）、核3行のチップ表示（2266行付近）を外す
- データに値が残っていれば消さずにそのまま（0件なので実質なし）。新しく書かれない

## 2. 古い写しの片付け（決定6）

### 2-1. Lectica 壁打ちプロンプトの埋め込み（Reflect OS・ランチャー）
- `LX_PROMPT_SPARRING`（v3.1・2026-09-19 の全文）が `reflect-os/index.html` と `launcher/index.html` に埋め込まれ、コピーボタンで古い版が出る。正本は Drive 00「Lectica実験_壁打ちプロンプト_v4.3.md」
- 埋め込みの全文を外し、コピーボタンの場所には案内1行「最新版は Drive の 00_ルール・仕様『Lectica実験_壁打ちプロンプト_最新版』を開いてください」（ボタンは外す。文はコピーできる普通の文字）
- `LX_PROMPT_SUMMARY`（まとめ用）も同じ扱いにするかは、使われ方を見て判断し報告（使われていれば残す）

### 2-2. Reflect の「決定検証」（`expType:'review'`）
- 10/26 にメニューから外し、データは0件（11/3 バックアップ）。コードに例外（`tkIsReview` など）が約30か所
- 分岐・例外・表示・取り込み（REFLECT-IMPORT の決定検証の登録 1544行付近を含む）を外す。`tkIsReview` は常に false を返す形に縮めてから呼び出し元を整理してよい
- 既存データに `expType:'review'` が見つかった場合（古いバックアップの復元など）は、起動時に通常の実験として扱い（`expType` を外す）、記録に「（旧 決定検証）」1行。退避キー `reflect_backup_review_20261103`

### 2-3. ヒトメモの日次ファイル（`daily-people`／`daily-contacts`）の受け口
- 10/4 に日次更新をやめた。同じ形の JSON は受信箱（`targetOS: hitomemo`）からも入るので入口が二重
- Drive の `daily-people.json`／`daily-contacts.json`（旧名 `aix-hitomemo` のフォールバックを含む）を読む処理と、そのボタン・自動読み込みを外す。受信箱の受け口（同じ JSON の取り込み部品）は残す
- 冪等キー（`hitomemo_aix_imported`）はデータ契約にあるので消さない

## 3. SU の見直し記録をバックアップへ（決定7）

- 記録の地図 §A：SU の見直し記録の2キー（`socialUniverse_snapshots`・`su_pending_review`。実際のキー名は SU のコードで確かめる）がバックアップに入っていない
- Task OS の全OSバックアップ（`collectAllOSData`）に `socialUniverseReview: { snapshots: jGet(...), pendingReview: jGet(...) }` を足し、復元側と復元前の退避対象（`RG_KEYS`）にも足す
- CLAUDE.md のデータ契約にそのキーを追記

## 4. 受入条件

1. Project OS の編集モーダルに「Reflect の問い」欄が無く、チップも出ない。ほかの欄は今までどおり
2. Reflect OS・ランチャーに v3.1 の全文が無く、案内1行が出る。コンソールエラー0
3. Reflect OS のコードに決定検証の分岐が無い。`expType:'review'` を含む古いデータを入れて起動すると通常の実験になり、退避キー1つ・二度走らない。探求ボード・上限・R番号の動きは変わらない
4. ヒトメモで日次ファイルを読む処理が無い。受信箱の hitomemo 宛ての取り込みは今までどおり入る
5. バックアップに `socialUniverseReview` が出て、復元で戻る
6. 構文検証・pre-commit 通過・各OSの SW 版上げ（task-os は BUILD_VER も）

## 5. コミット

「project-os/reflect-os/launcher/hitomemo/task-os: 使っていない欄と古い写しの片付け（Project の Reflect問いID欄、Lectica壁打ちプロンプト v3.1 の埋め込み、Reflect の決定検証、ヒトメモの日次ファイルの受け口）。SU の見直し記録をバックアップへ（11/3 本人決定）」

## 6. 報告

変更箇所／`LX_PROMPT_SUMMARY` の扱い／受入6項目。実装を止める場合のみ質問を1つ。
