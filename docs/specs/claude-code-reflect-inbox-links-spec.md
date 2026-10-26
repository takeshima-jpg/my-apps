# Claude Code 実装依頼書：Reflect OS の受信箱対応 ＋ 紐づけ（links）の保存（依頼書 2／8）

作成日：2026-10-26（メンテナンス担当）
対象：`reflect-os/index.html` のみ
土台：main `9327ea8`（Task OS ハブ配置済み）。作業前に `git pull`。
共通仕様：`claude-code-shared-inbox-spec.md`（配置済み）／コピー元：`task-os/index.html` 2232–2310 行「受信箱 共通部品 v1」
地図：`記録の地図_v1.1_2026-10-26.md` §D-2（紐づけ行の書式）

---

## 1. 受信箱の受け口

### 1-1. 共通部品をコピー
- Task OS の「受信箱 共通部品 v1」ブロック（2232–2310）を**そのまま**コピーし、`INBOX_OS = 'reflect'` だけ変える
- Reflect のデータ（`reflectOS_v1`）の読み込みが終わった後（boot 完了後・`tkMigrate` の後）に `inboxProcess('load')` を呼ぶ
- `?inbox=1` で開かれたとき（Task OS の非表示 iframe）：復元ガードの確認ダイアログ・`alert`・`confirm` を一切出さない。`lxImportSave` の失敗 `alert` も、`inbox=1` のときはメッセージを返り値にして `ok:false` に流す

### 1-2. `inboxApply(block, links, item)`
既存の `registerAiInput()`（1278行〜）の本体を、**textarea と status 要素に依存しない関数** `reflectImportText(text, opts)` に切り出し、画面の「登録」ボタンと受信箱の両方から呼ぶ（挙動は変えない）。

```js
async function inboxApply(block, links, item){
  const r = await reflectImportText(block, {silent:true});   // {ok, summary, logIds:[], lecticaLogIds:[], questionIds:[], experimentIds:[]}
  if(!r.ok) return {ok:false, summary:r.summary};
  inboxAttachLinks(r, links);                                  // §2
  return {ok:true, summary:r.summary};                        // 例：'振り返り1件・問い2件・実験1件／Lectica L042 1件'
}
```
- `reflectImportText` の返り値に、作成・更新したレコードの id を入れる（汎用ログ `logs`、`tkMigrate` で生まれた問い・実験、Lectica 実践ログ）。`tkMigrate` が生んだ id を拾うため、`tkMigrate` は**今回作った id の配列を返す**ように変える（返り値を使っていない既存呼び出しは影響なし）
- 「【振り返り】も `---REFLECT-IMPORT---` も無い」「Lectica の実験IDが不明」など、既存の失敗条件はそのまま `ok:false` に（done にならず保留）
- 同じ `item.id` は共通部品が弾く。加えて Lectica 実践ログは既存の重複確認（同じ実験ID＋同じ実行日）のまま

## 2. 紐づけ（`links`）の保存

- 保存先（既存フィールドは変えず、任意の `links` を足す）：
  - 汎用ログ（`reflectOS_v1.logs[]`）：`links: { strategyGoalId, projectId, projectName, personIds, personNames, questionId }`（空の項目は入れない。何も無ければ `links` 自体を付けない）
  - その取り込みから `tkMigrate` で生まれた問い・実験：同じ `links` を付ける。ただし `questionId` は「元の問い」の意味なので、新しく生まれた**問い**には付けない（実験には付けてよい＝その問いの検証という意味）
  - Lectica 実践ログ（`lectica_experiment_logs_v1[]`）：同じ `links`
- `projectName` だけで `projectId` が無いとき：`localStorage['pos_v4']` を読めて、`name` が一致（前後空白無視・大文字小文字無視）するPJが**1つだけ**あれば `projectId` を補う。複数・0件なら名前だけ残す。`pos_v4` には**書かない**
- `personNames` だけのとき：`hitomemo_profiles_v1` で `lxNormName` 相当の正規化（括弧注記・空白・NFKC）で一致が1つだけなら `personIds` を補う。書かない
- 「⬇ 取り込む」画面からの手貼りでも、本文に「紐づけ：」行があれば同じように `links` を付ける（`inboxParseLinks` を使う）。行自体はログ本文に残ってよい（未知の行として扱われている現状どおり）

## 3. 表示（最小）
- ログ詳細・探求ボードの実験カード・Lectica ログに、`links` があれば **1行の薄いチップ列**：`S03 ③JSS承継税制`／`PJ JSS承継親孝行プロジェクト`／`👤 父`。S-ID の表示番号と名前は、`記録の地図` §D-1 の対応表を**定数 `STRATEGY_GOALS`** としてこのファイルに持つ（`{S01:{no:'①',name:'関連当事者取引解消（借金返済）'},…}`。地図が変わったら Claude Code が定数を直す）
- クリックで遷移はしない（Reflect からPJやヒトメモを開く導線は作らない。静かなUI）
- `links` が無いレコードは何も出さない

## 4. 変えないこと
- 取り込みブロックの書式・`parseAiReflect`／`lxParseImport` の解析結果・`tkMigrate` の冪等（`sourceCk`）
- `reflect_focus_v1` の形式
- 探求ボードの上限・入れ替えモーダル
- Service Worker の挙動（版だけ上げる）

## 5. 受入条件（playwright。`import_inbox_v1` に直接 item を置く）
1. `targetOS:'reflect'`、`block` に【振り返り】（問い1・次の実験1）＋末尾「紐づけ：S03 ③JSS承継税制／PJ：JSS承継親孝行プロジェクト／人：父」を置いて Reflect を単体で開く → ログ1件・問い候補1・実験候補1が増え、ログと実験に `links`（`strategyGoalId:'S03'`、`projectName`、`personNames:['父']`。`pos_v4` に同名PJがあれば `projectId` も）が付き、問いには `questionId` が付かない。`import_inbox_done_v1` に id が入り、再読み込みしても二重にならない
2. 同じ item を `?inbox=1` の iframe 経由（Task OS から）で処理 → ダイアログが出ず、Task OS HOME に「振り返り1件・問い1件・実験1件」の行が出る
3. `---REFLECT-IMPORT---` の Lectica 結果ブロック（L042・実行日・気づき）＋紐づけ行 → `lectica_experiment_logs_v1` に1件追加され `links` が付く。同じ実行日の同じ実験IDをもう一度 → 既存の重複確認どおり追加されず、`ok:false` ではなく「重複のため追加なし」を `ok:true` の summary で返す（done にする）
4. 【振り返り】も REFLECT-IMPORT も無い本文 → `ok:false`・保留・ダイアログなし
5. 画面の「⬇ 取り込む」から紐づけ行つきで手貼り → 1 と同じ `links` が付く。紐づけ行の無い手貼りは従来どおり（`links` 無し）
6. `links` 付きのログ・実験カードにチップ列が出る。無いものには出ない。375px で崩れない
7. 既存データ（`reflectOS_v1`）が改修前後で変わらない（起動だけでは保存が走らない）
8. 構文検証 OK・コンソールエラー 0・SW 版上げ

## 6. コミット
「reflect-os: 受信箱（import-inbox）の受け口を追加（共通部品 v1・既存の取り込みパーサをそのまま使用・inbox=1 ではダイアログなし）。取り込んだログ・問い・実験・Lecticaログに紐づけ links（戦略目標 S-ID／PJ／人／問い）を保存し、薄いチップで表示。pos_v4・hitomemo は名前→ID の照合に読むだけ」

## 7. 報告
変更箇所／`reflectImportText` の切り出し内容／受入条件8項目／実装を止める場合のみ質問を1つ。
