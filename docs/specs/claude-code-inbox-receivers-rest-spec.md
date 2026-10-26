# Claude Code 実装依頼書：受信箱の受け口（残りのOS）— KOSOLog／ヒトメモ／1day／Routine／100LIST／SU・学びレーダー（依頼書 4・5・6・8 をまとめたもの）

作成日：2026-10-26（メンテナンス担当）
対象：`koso-log/index.html`、`hitomemo/index.html`、`1day/index.html`、`routine-os/index.html`、`100list/index.html`、`social-universe/index.html`、`learning-radar/index.html`
土台：main `c02cf52`（Task OS ハブ `9327ea8`・Reflect `aa51f8e`・Project `89f859f` 配置済み）。作業前に `git pull`。
共通仕様：`claude-code-shared-inbox-spec.md`／コピー元：`task-os/index.html` 2232–2310 行「受信箱 共通部品 v1」（`INBOX_OS` の1行だけ差し替え）
**配置は1OSずつ commit**（順番：KOSOLog → ヒトメモ → 1day → Routine → 100LIST → SU・学びレーダー）。各OSの共通事項：`?inbox=1` ではダイアログ・alert・confirm を出さない／データ読み込み後に `inboxProcess('load')`／既存の取り込みパーサをそのまま使う／`links` は取り込みで作成・更新したレコードに任意で付ける（何も無ければ付けない）／SW があれば版上げ／375px・44px・コンソールエラー0・構文検証

---

## 4. KOSOLog（`INBOX_OS='koso'`）

- `inboxApply`：`registerAiInput()`（1455行〜）の本体を textarea に依存しない `kosoImportText(text, {silent:true})` に切り出し、受信箱と画面の両方から呼ぶ。返り値 `{ok, summary, touchedIds:[G03,E08,…]}`。**退避（`kouso_backup_lastimport`）と「直前の取り込みを元に戻す」は受信箱経由でも同じに効かせる**
- `summary` は既存の要約（「G03 更新（記録2件）／G06 新規…」）をそのまま
- 読めるブロックが1つも無い → `ok:false`。一部読めない → `ok:true` で summary に「読めませんでした：…」を含める（既存どおり）
- `links`：`touchedIds` の構想・試しに付ける。KOSOLog は PJ化で `projectId` を持つので、`links.projectId` があり構想の `projectId` が空なら**補わない**（PJ化は本人の操作で決めるため。`links` に残すだけ）
- 表示：構想詳細の「関連チップ」の並びに `S03 ③JSS承継税制`・`👤 父` を同じ見た目で足す（`STRATEGY_GOALS` 定数は Reflect・Project と同じ内容をここにも持つ）

## 5. ヒトメモ（`INBOX_OS='hitomemo'`）

- 受け付ける `block`：既存の AI更新読込と同じ JSON（`{"people":[…]}` または `{"contacts":[…]}`、両方を1つに持つ `{"people":[…],"contacts":[…]}` も可）。既存の適用関数（daily-people／daily-contacts を適用している関数。冪等台帳 `hitomemo_aix_imported`）を**そのまま呼ぶ**。Markdown の取り込み書式は新設しない
- `block` が JSON として読めない → `ok:false`
- `summary`：「人物 n件・接点 m件（うち既存 k件はスキップ）」
- `links`：接点・人物のレコードに `strategyGoalId`／`projectId`／`projectName` を付ける（`personIds` はヒトメモ自身なので付けない）。表示は人物詳細の接点行に薄いチップ（PJ名・S-ID）
- Drive の AI更新読込（既存）はそのまま残す。受信箱は「担当が出す個別の更新」用

## 6. 1day（`INBOX_OS='oneday'`）

- **直接は書かない。** 受け付ける `block` は AIX 下書きと同じ JSON `{ "targetDate":"YYYY-MM-DD", "events":"…", "unease":"…", "flags":[…] }`。`inboxApply` はこれを `aix_drafts` に**下書きとして追加**（同じ `targetDate` があれば置き換え・既存の `_aixSaveDrafts` と同じ形）し、`ok:true, summary:'m/d の下書きを追加（承認待ち）'` を返す。保存は本人が AIX 承認フォームで承認したとき（1day を重くしない・本人が手で選ぶ原則）
- `links` は下書きに持たせ、承認時にログへ引き継ぐ（`oneday_logs_v1` の要素に `links`・任意）。手で書いた記録には付けない。表示はログカードに薄いチップ1行（`links` があるときだけ）
- `block` が JSON でない・`targetDate` が無い → `ok:false`

## 7. Routine OS（`INBOX_OS='routine'`）

- 受け付ける `block`：既存の ROUTINE-IMPORT（`【ROUTINE-IMPORT】 {json} 【/ROUTINE-IMPORT】`）。`riParseJson` → `riRun(payload, true)` を**プレビューなしで適用**（受信箱に入る時点で本人の OK を経ているため。冪等は `appliedOps`）。`summary` は `riRun` の `out.summary`
- 適用対象0件（すべて適用済み）→ `ok:true`・summary「適用するものはありません」（done にする）
- 読めない → `ok:false`
- `links`：ルーチンの定義（`routineOS_tasks` の要素）に任意で付ける。表示は追加しない（Routine は静かなまま）
- Task OS のサイドバー iframe（`#frame-routine`）常駐なので、合図を受けたら適用後に一覧を再描画

## 8-1. 100LIST（`INBOX_OS='list100'`）

- 書式（新設。Task OS ハブの保留文言「【やりたいこと】」と合わせる）：
```
---LIST100-IMPORT---
やりたいこと：〇〇（この行ごとに1件。続く行はその件に掛かる）
カテゴリ：〇〇（任意・CATS にある名前のときだけ。無ければ未分類）
メモ：〇〇（任意）
---END---
```
- `inboxApply`：行ごとに `addItem({title, category, memo})`（既存の追加関数。`no`・`id` は既存の採番）。同じ `title` が未完了で既にあれば追加せず summary に「重複：…」
- `links`：追加した項目に任意で付ける。表示は追加しない
- **Task OS 側**：ハブで `【やりたいこと】`／`---LIST100-IMPORT---` を含む `targetOS:'taskos'` の item は `targetOS:'list100'` に振り替えて iframe（`../100list/index.html?inbox=1`）へ渡す（担当が `taskos` 宛てで出しても届くように）。Task OS の既存の保留文言は外す

## 8-2. ソーシャルユニバース（`INBOX_OS='su'`）・学びレーダー（`INBOX_OS='learning'`）

- 共通部品を入れ、`inboxApply` は **`{ok:false, summary:'このOSには取り込み口がありません。本文をコピーして手で反映してください'}` を返すだけ**（受け口だけ・保留に残る・Task OS HOME に本文コピーの退路が出る）
- SU は四半期の紙運用、学びレーダーは Drive ファイル経由（learning-events／learning-check）が既にあるため、取り込みブロックの新設はしない
- `links` の保存もしない（今回は受け口のみ）

---

## 受入条件（OSごと。`import_inbox_v1` に直接 item を置いて単体起動と Task OS 経由の両方）
- KOSOLog：KOSO-IMPORT（G03 更新＋新規1）＋紐づけ行 → 更新・新規が入り `links` が付く。再実行で二重にならず、「直前の取り込みを元に戻す」で戻る
- ヒトメモ：`{"people":[1件],"contacts":[1件]}` → 追加され台帳で冪等。JSON でない本文は保留
- 1day：下書き JSON → `aix_drafts` に1件増え、承認フォームに出る。承認するとログに `links` 付きで保存。`oneday_logs_v1` は承認前に変わらない
- Routine：ROUTINE-IMPORT の ops 2件 → 適用され `appliedOps` に入る。同じ ops を再送 → 「適用するものはありません」で done
- 100LIST：やりたいこと2件（1件は既存と同名）→ 1件追加・1件重複。Task OS 経由で `taskos` 宛てに `【やりたいこと】` を含む item → `list100` に振り替わり取り込まれる
- SU・学びレーダー：宛ての item が保留に残り、HOME に「取り込み口がありません」と本文コピー
- 全OS：`?inbox=1` でダイアログが出ない／既存データが起動だけでは変わらない／375px・44px・コンソールエラー0・構文検証OK

## コミット（OSごと）
「{os}: 受信箱（import-inbox）の受け口を追加（共通部品 v1・既存の取り込み経路をそのまま使用・inbox=1 ではダイアログなし）。取り込んだレコードに紐づけ links（任意）」。SU・学びレーダーは「受け口のみ（取り込み口なし＝保留）」と書く

## 報告
OSごとに：変更箇所／切り出した関数名／受入条件の結果。実装を止める場合のみ質問を1つ（OS名と経緯つきで）。
