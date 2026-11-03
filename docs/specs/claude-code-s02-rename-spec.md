# Claude Code 実装依頼書：戦略目標 S02 の名前を「スリーエーグループ2030構想」に／紐づけの古いPJ名をそろえる

作成日：2026-11-03（メンテナンス担当。本人決定 11/3）
対象：`STRATEGY_GOALS` を持つ5ファイル（`reflect-os`／`project-os`／`koso-log`／`hitomemo`／`1day`）＋ 紐づけ（`links`）を保存・表示するOS（上の5つと `task-os`）
土台：main `63a370d`。作業前に `git pull`。

---

## 背景（なぜ）

- PJ「3AHD2030構想」（Project OS の実ID `s6n9vf1vgdx`）は「スリーエーグループ2030構想」に名前が変わった（10/31 の取り込みで反映済み・旧名は `formerNames`）
- 本人決定（11/3）：**戦略目標 S02 の名前も「②3AHD構想作成」→「②スリーエーグループ2030構想」**に。記録の地図の S-ID 対応表と、各OSの紐づけに残っている古い名前もそろえる
- 10/31 のバックアップで、紐づけの `projectName:"3AHD2030構想"` が残っている場所：受信箱の記録（`import_inbox_log_v1`）6件・Reflect の問い2件・実験1件・KOSOLog の構想1件。ほかのOSにもあり得る

## 1. `STRATEGY_GOALS` の S02（5ファイル同時）

- `S02:{no:'②', name:'3AHD構想作成'}` → `S02:{no:'②', name:'スリーエーグループ2030構想'}`
- S-ID（`S02`）と表示番号（②）は変えない。ほかの S01・S03〜S05 は変えない
- 5ファイルとも同じ内容に（地図 §D-1 と一致）

## 2. 紐づけに残っている古いPJ名を直す（起動時1回・冪等・各OS）

- 対象：各OSが保存している `links`（とその配列）で、**`projectId === 's6n9vf1vgdx'` または `projectName === '3AHD2030構想'`** のもの → `projectName` を `'スリーエーグループ2030構想'` に（`projectId` が無ければ `'s6n9vf1vgdx'` を足す）
  - Reflect OS：問い・実験・ログ・テーマ・原則、Lectica の実践ログ（`lectica_experiment_logs_v1`）の `links`
  - KOSOLog：構想・試しと、その記録（`log[]`）の `links`
  - Project OS：ムーブ等の `links`
  - ヒトメモ・1day：保存している `links`
  - Task OS：受信箱の記録 `import_inbox_log_v1` の `links`（`title`・`summary` の文面は履歴なので変えない）、受信箱の未処理 `import_inbox_v1` の `links`
- 各OSで、実行前に元のキーを `{OS}_backup_s02rename_20261103` に退避（同名キーがあれば作らない）、実行済みフラグ `{OS}_s02rename_20261103_done`。直した件数が1件以上なら console に件数（トーストは不要）
- 本文中の文字（記録の本文・ムーブの本文など）は**変えない**（言った時点の記録として残す）

## 3. これからずれないように（表示）

- 紐づけのチップ（Reflect の `rfLinkChips` など、各OSで `links` を表示している所）は、`projectId` があれば **Project OS（`pos_v4`）の今の名前を優先**して出し、見つからないときだけ `projectName` を出す（PJ名が変わっても表示が古いままにならない）
- 取り込みの紐づけ行で旧名（`formerNames`）が書かれても、保存する `projectName` は Project OS の今の名前にする（`projectId` で引けた場合）

## 4. 受入条件（playwright・10/31 以降のバックアップ相当のデータ）

1. 5ファイルの `STRATEGY_GOALS.S02.name` が「スリーエーグループ2030構想」。紐づけのチップが「S02 ②スリーエーグループ2030構想」と出る
2. 起動後、各OSの `links.projectName` に「3AHD2030構想」が0件（バックアップで確認）。退避キーが各1つ、再読み込みで二度走らない。本文は変わらない
3. 紐づけ行に `PJ：s6n9vf1vgdx 3AHD2030構想` と書いた取り込みでも、保存される `projectName` は「スリーエーグループ2030構想」
4. Project OS でPJ名を仮に変えると、チップの表示がその名前になる（戻して確認）
5. 構文検証OK・コンソールエラー0・各OSの SW 版上げ（task-os は BUILD_VER も）

## 5. コミット

「reflect-os/project-os/koso-log/hitomemo/1day/task-os: 戦略目標 S02 の名前を『スリーエーグループ2030構想』に（PJの改名に合わせる・11/3 本人決定）。紐づけに残る旧PJ名『3AHD2030構想』を起動時1回だけ直す（本文は変えない・退避あり）。紐づけのチップは projectId から今のPJ名を引いて表示」

## 6. 報告

変更箇所／OSごとに直した件数／受入5項目。実装を止める場合のみ質問を1つ。配置後、メンテナンス担当が記録の地図 §D-1 を直し、VISION見直し担当へ知らせる。
