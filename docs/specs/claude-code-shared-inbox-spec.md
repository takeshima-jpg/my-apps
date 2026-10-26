# Claude Code 実装依頼書：受信箱（import-inbox）の共通仕様 と Task OS ハブ

作成日：2026-10-26（メンテナンス担当。VISION見直し担当の申し送り「記録の背骨」§4・§6 の 1 と 7 を1本にしたもの）
対象：`task-os/index.html`（ハブ・主）、各OSに入れる**共通部品**（本依頼書で定義。OSごとの組み込みは別依頼書 2〜6・8）
土台：main `f4606a1`。作業前に `git pull`。
正本の地図：`記録の地図_v1.0_2026-10-26.md`（Drive 00_ルール・仕様）
関連：`docs/specs/claude-code-cockpit-autoimport-spec.md`（未実装）は本依頼書に統合して閉じる

---

## 0. ねらい と 前提

- いま Cowork の各担当（PJ見直し／構想見直し／リフレクト見直し／VISION見直し）は取り込みブロックを**チャットに出し、本人が各OSに貼っている**。これを、担当が Drive の受信箱に置き、**Task OS を開けば（同期すれば）全部入る**形にする
- 前提（コードで確認済み）：
  - 全OSは同じ公開元（takeshima-jpg.github.io）なので **localStorage を共有**している。Drive を読めるのは Task OS・ヒトメモ・Project（シート用）・学びレーダー・Brief Viewer だけで、Reflect・KOSOLog・Routine・SU・1day・100LIST・Shot は読めない → **Drive を読むのは Task OS だけ**にし、各OSには localStorage 経由で渡す
  - Cowork の Drive コネクタは同名ファイルへの追記・更新・削除ができない（新規作成のみ） → 受信箱は **1回の書き込み＝1ファイル**、処理済みの管理は OS 側だけで行う
  - 取り込みブロックのパーサは各OSに既にある（Reflect `parseAiReflect`／Project `piApply` 系／KOSOLog `registerAiInput` 系／Routine ROUTINE-IMPORT）。**受信箱はそのパーサを呼ぶだけ**で、書式は変えない
- 守ること：Cowork はOSに書かない／本人の「OK」の後に担当が受信箱へ書く／催促・件数バッジを足さない／既存データを壊さない／未知の行・未知のフィールドは無視

---

## 1. Drive 側：受信箱ファイル

- 置き場：10_日次データ（`1qOQXKraLlYA8BA3WM1dvNdVGzHasRWKP`）
- ファイル名：`import-inbox-YYYY-MM-DD-{担当}.json`（例：`import-inbox-2026-10-28-pj.json`。担当＝`pj`／`koso`／`reflect`／`vision`／`brief`）。同日に2回書けば末尾に `-2` など。**Task OS は名前が `import-inbox` で始まるファイルをすべて読む**
- 中身：
```json
{
  "version": 1,
  "source": "PJ見直し",
  "createdAt": "2026-10-28T09:12:00+09:00",
  "items": [
    {
      "id": "pj-20261028-01",
      "createdAt": "2026-10-28T09:12:00+09:00",
      "source": "PJ見直し",
      "targetOS": "project",
      "title": "JSS承継親孝行PJ：見立て更新と記録2件",
      "block": "---PROJECT-IMPORT---\nPJ: JSS承継親孝行プロジェクト\n...\n紐づけ：S03 ③JSS承継税制／PJ：JSS承継親孝行プロジェクト／人：父\n",
      "links": { "strategyGoalId": "S03", "projectName": "JSS承継親孝行プロジェクト", "personNames": ["父"] }
    }
  ]
}
```
- `id`：冪等キー。担当名＋日付＋連番。**同じ id は二度と処理しない**
- `targetOS`：`reflect`／`project`／`koso`／`routine`／`hitomemo`／`oneday`／`taskos`（Shot・100LIST）／`su`／`learning`。Brief Viewer・コックピットは宛先にならない
- `title`：Task OS HOME に出す1行（40字程度）。担当が書く
- `block`：各OSの取り込み口に貼るのと**同じ本文**。末尾に紐づけ行（地図 §D-2）があってよい
- `links`：担当が分かる範囲で。`strategyGoalId`／`projectId`／`projectName`／`personIds[]`／`personNames[]`／`questionId`。空のものは入れない
- `status`／`doneAt` は **Drive 側には持たない**（Cowork が更新できないため）

## 2. 共通キー（localStorage・全OS共有）

| キー | 持ち主 | 中身 |
|---|---|---|
| `import_inbox_v1` | Task OS が書く・各OSが自分宛てを消す | `{ updatedAt, items:[ 上の item と同形 ] }`。未処理だけ |
| `import_inbox_done_v1` | 各OS・Task OS が追記 | `[ { id, os, doneAt, summary } ]`。新しい順・最大2000件 |
| `import_inbox_log_v1` | 各OS・Task OS が追記 | HOME カード用。`[ { date, os, title, summary, links, id } ]`。直近60日分だけ保持 |

バックアップ：`collectAllOSData()` に `importInbox: { pending: jGet('import_inbox_v1'), done: jGet('import_inbox_done_v1'), log: jGet('import_inbox_log_v1') }` を追加。`restoreAllOSData` と `RG_KEYS` にも3キーを追加。Morning Brief は `importInbox.pending.items.length` を「受信箱に未取り込み n件（内訳）」の事実1行に使える（Brief 側の申し送りは別途）

## 3. 共通部品（各OSに同じものを入れる。コピー元は Task OS に置く関数群）

Task OS に `/* ══ 受信箱 共通部品 v1 ══ */` のブロックとして書き、各OSの依頼書では「Task OS の同ブロックをそのままコピーし、`INBOX_OS` と `inboxApply` だけ差し替える」と指示する。

```js
const INBOX_OS = 'project';                      // このOSの targetOS 名
const INBOX_KEY='import_inbox_v1', INBOX_DONE='import_inbox_done_v1', INBOX_LOG='import_inbox_log_v1';
function inboxRead(){ try{ return JSON.parse(localStorage.getItem(INBOX_KEY)||'null')||{items:[]}; }catch(e){ return {items:[]}; } }
function inboxDoneSet(){ try{ return new Set((JSON.parse(localStorage.getItem(INBOX_DONE)||'[]')).map(d=>d.id)); }catch(e){ return new Set(); } }
function inboxMarkDone(item, summary){
  // done に追記（最大2000・新しい順）、pending から除去、log に追記（60日）
}
function inboxParseLinks(block){
  // 「紐づけ：」で始まる行を探し、S-ID／PJ：／人：／問い： を切り出して links を返す（item.links とマージ。item.links 優先）
  // 書式：紐づけ：S03 ③JSS承継税制／PJ：{id} {名前}／人：{id} {名前}, {id} {名前}／問い：{id}
}
async function inboxProcess(trigger){            // trigger: 'load' | 'message'
  const box=inboxRead(); const done=inboxDoneSet();
  const mine=(box.items||[]).filter(it=>it&&it.targetOS===INBOX_OS&&!done.has(it.id));
  const results=[];
  for(const it of mine){
    try{
      const links=inboxParseLinks(it.block||''); Object.assign(links, it.links||{});
      const r=await inboxApply(it.block||'', links, it);   // OSごとに実装。{ok:true, summary:'G03 更新（記録2件）'} / {ok:false, summary:'理由'}
      if(r&&r.ok){ inboxMarkDone(it, r.summary); results.push({id:it.id, ok:true, summary:r.summary}); }
      else results.push({id:it.id, ok:false, summary:(r&&r.summary)||'取り込めませんでした'});
    }catch(e){ results.push({id:it.id, ok:false, summary:'エラー: '+(e&&e.message||e)}); }
  }
  if(window.parent!==window){ try{ window.parent.postMessage({type:'myapps-inbox-result', os:INBOX_OS, trigger, results}, location.origin); }catch(e){} }
  return results;
}
window.addEventListener('message', ev=>{ if(ev.origin!==location.origin) return; if(ev.data&&ev.data.type==='myapps-inbox-process') inboxProcess('message'); });
// 起動時：自分のデータの読み込みが終わった後に inboxProcess('load')（Task OS を経由しなかった日の保険）
```

`inboxApply(block, links, item)` の各OSでの中身（別依頼書で詳細化）：
- **既存の貼り付けパーサをそのまま呼ぶ**（textarea に入れてボタンを押すのと同じ経路。DOMを経由しない関数に切り出せるなら切り出す）
- 取り込みで作成・更新したレコードに `links` を保存する（フィールド名はOSの命名に合わせる。`projectName`／`personNames` しか無いときは名前一致で実IDを引き、引けなければ名前だけ保存）
- 失敗（パーサが読めない・対象IDが無い）は `{ok:false, summary}` を返し、**done にしない**（Task OS HOME に「保留」で出る。次回また試す。3回失敗したら HOME に「手で貼ってください」と出す＝その item の `block` をコピーできるボタン付き）
- 冪等：同じ `id` は done で弾く。パーサ側の冪等（KOSO の記録二重防止・Routine の appliedOps 等）はそのまま効かせる

## 4. Task OS ハブ

### 4-1. 受信箱を Drive から取る（`gdAutoSync` の最後に追加・手動同期でも実行）
- `'${GD_DAILY_FOLDER_ID}' in parents and name contains 'import-inbox' and trashed=false`、`createdTime` が直近60日のものを一覧（`gdFindInFolder` の派生でよい）
- すべてダウンロードして `items` を結合。`id` で重複除去（同じ id は `createdAt` の新しい方）。`import_inbox_done_v1` にある id は除外
- `import_inbox_v1` を**上書き**（未処理だけ）。失敗（権限・ネット）しても同期全体は止めない（警告ログのみ）
- 処理済みファイルの削除・更新は**しない**（Drive の掃除は月次で手動）

### 4-2. 宛先OSだけ開いて合図する（案C）
- `import_inbox_v1` の未処理を `targetOS` ごとに数え、**宛先のあるOSだけ**処理する
  - `taskos`：Task OS 自身の `inboxProcess`（Shot 追加／100LIST 追加）
  - `routine`／`shot`／`project`：既存のサイドバー iframe（`#frame-routine` など）が読み込み済みならそこに `postMessage`。未読み込みなら `src` を付けて読み込み完了後に送る
  - `reflect`／`koso`／`hitomemo`／`oneday`／`su`／`learning`：非表示 iframe（`display:none`・`#inbox-frame-{os}`）を1つ作り `../{os}/index.html?inbox=1` を読み込み、`load` 後に `postMessage({type:'myapps-inbox-process'}, location.origin)`。結果を受けたら iframe を外す
- 結果の受信：`message` で `myapps-inbox-result`（origin 一致のみ）。`ok:true` は各OS側で done 済みなので Task OS は `import_inbox_log_v1` を読み直すだけ。**15秒**応答が無ければ諦めて次回（pending のまま）
- 同期中に二重起動しないようフラグを持つ。宛先が1件も無い日は**何もしない**（iframe も作らない）
- `?inbox=1` で開かれたOSは、Service Worker・自動復元ガード等の起動時ダイアログを出さない（確認モーダルが出る作りのOSは、`inbox=1` のときはスキップ。各OS依頼書で指定）

### 4-3. HOME「📥 今回取り込んだもの」カード
- `import_inbox_log_v1` の**直近7日**を、新しい順に最大10行：`m/d {宛先OS} {title}｜{summary}｜{紐づけ：S03 ③JSS承継税制・PJ名・人名}`。クリックでそのOSを開く（`nav('reflect')` 等）
- 未処理（`import_inbox_v1` に残っているもの）は同じカードの下に「保留」として `title` と理由（`summary`）、**3回以上失敗したものだけ**「📋 本文をコピー」ボタン（手で貼る退路）
- 7日以内の取り込みも保留も無ければ**カードごと非表示**。件数バッジ・「未取り込み n件」の見出し・色の警告は出さない（HOME v2 の方針どおり）
- 配置：`homeFocusCard`（重点の問い）の下

### 4-4. 設計の根拠（UI10法則）
- ヒック：本人の操作は「Task OS を開く（同期）」だけ。選択肢を足さない
- ヤコブ：各OSの取り込みは既存の貼り付けと同じパーサ・同じ結果。画面の操作感を変えない
- ゲシュタルト：取り込まれたものはOS別ではなく時系列1本で、紐づけ（戦略目標・PJ・人）を同じ行に
- 損失回避：失敗は消さず保留に残し、本文をコピーして手で貼れる退路を必ず置く

## 5. 変えないこと
- 各OSの取り込みブロックの書式・パーサの挙動（REFLECT／PROJECT／KOSO／ROUTINE-IMPORT）
- 各OSの「⬇ 取り込む」画面（残す。受信箱は裏で同じパーサを通す）
- `daily-brief.json`／`daily-tasks.json`／`daily-contacts.json` の既存の流れ（1day の AIX 承認・Task OS の AIタスク読込・ヒトメモの AI更新読込はそのまま。受信箱に寄せるのは**担当の取り込みブロック**だけ。これらを受信箱へ移すかは別途）
- Drive 上の受信箱ファイルの更新・削除

## 6. 受入条件（playwright。Drive は読めないので、`import_inbox_v1` に直接 item を置いて検証。Drive 取得部は手動同期で実機確認）
1. `import_inbox_v1` に `targetOS:'taskos'` の Shot 追加ブロックを1件置いて Task OS を開く → Shot が1件増え、`import_inbox_done_v1` に id が入り、`import_inbox_v1` から消え、HOME カードに1行出る。再読み込みしても二重に増えない
2. `targetOS:'project'` の PROJECT-IMPORT を1件置く → Task OS が `#frame-project` に合図し、Project OS 側の `inboxProcess` が既存パーサで取り込み、結果が HOME に出る（この項目は Project の依頼書 3 の配置後に有効。共通部品の組み込み前は「保留：宛先OSが未対応」と出て止まらないこと）
3. 宛先の無い状態で Task OS を開く → iframe が作られず、HOME にカードが出ない
4. 読めないブロック（`---PROJECT-IMPORT---` の無い本文）→ `ok:false` で保留に残る。3回目から「📋 本文をコピー」ボタンが出る。done には入らない
5. `inboxParseLinks('…\n紐づけ：S03 ③JSS承継税制／PJ：abc123 JSS承継親孝行プロジェクト／人：h1 父, h2 前田さん／問い：q9')` → `{strategyGoalId:'S03', projectId:'abc123', projectName:'JSS承継親孝行プロジェクト', personIds:['h1','h2'], personNames:['父','前田さん'], questionId:'q9'}`。「紐づけ：」行が無ければ `{}`。`PJ：JSS承継親孝行プロジェクト`（ID無し）→ `projectName` だけ
6. 全OSバックアップに `importInbox.pending/done/log` が入り、復元で戻る。`RG_KEYS` に3キーがある
7. 15秒応答が無い宛先（iframe の読み込みを故意に失敗させる）→ pending のまま、Task OS の同期は完了する
8. 375px で HOME カードが崩れない。コンソールエラー 0。構文検証 OK。`BUILD_VER` を当日に

## 7. 後続の依頼書（この後に出す。各OSは「共通部品をコピー＋`inboxApply` を書く＋`links` を保存」の小さな依頼）
2 Reflect（Lectica 含む）／3 Project（＋「答え合わせする」印・「Reflect問いID」欄・関係者のヒトメモID・「戦略目標 S-ID」欄）／4 KOSOLog／5 ヒトメモ／6 1day（受信箱経由のみ `links`・手入力欄は足さない）／8 Routine・SU・学びレーダー・100LIST（受け口のみ。パーサが無いOSは `{ok:false, summary:'このOSには取り込み口がありません'}` を返して保留＝手で扱う）
動作確認の順番：**Reflect と Project から**（本人決定 10/26）

## 8. コミット
「task-os: 受信箱（import-inbox）のハブを追加。Drive 10_日次データの import-inbox-*.json を同期時に読み import_inbox_v1 へ、宛先OSだけ非表示iframe＋postMessageで取り込みを合図、結果を HOME『📥 今回取り込んだもの』に時系列表示（該当なしは非表示・催促なし・失敗は保留と本文コピーの退路）。共通部品 v1（inboxProcess／inboxParseLinks）を同梱し、バックアップに importInbox を追加。cockpit-autoimport-spec はこれに統合」

## 9. 報告
変更箇所／共通部品ブロックの行範囲（各OS依頼書がコピー元として参照する）／受入条件8項目／実装を止める場合のみ質問を1つ。
