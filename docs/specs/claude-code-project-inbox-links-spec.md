# Claude Code 実装依頼書：Project OS の受信箱対応 ＋ 紐づけ（links）＋ 戦略目標 S-ID・Reflect問いID・関係者ID・「答え合わせする」印（依頼書 3／8）

作成日：2026-10-26（メンテナンス担当）
対象：`project-os/index.html` のみ
土台：main `9327ea8`。作業前に `git pull`。
共通仕様：`claude-code-shared-inbox-spec.md`／コピー元：`task-os/index.html` 2232–2310 行
地図：`記録の地図_v1.1_2026-10-26.md` §B・§D

---

## 1. 受信箱の受け口

- Task OS の「受信箱 共通部品 v1」をそのままコピーし `INBOX_OS = 'project'`。`pos_v4` 読み込み後に `inboxProcess('load')`
- Project は Task OS のサイドバー iframe（`#frame-project`）として常駐しているので、`message` での合図を受けたら `inboxProcess('message')` → 取り込み後に表示中の画面を再描画
- `?inbox=1` のときは復元ガードのダイアログ・`alert`・`confirm`・PJ候補の選択UIを出さない（§1-2）

### 1-2. `inboxApply(block, links, item)`
既存の `piParse()`（1726行〜）は textarea と status 要素に依存しているので、**解析だけを行う `piParseText(text)`** に切り出す（返り値 `{pjName, items, error}`。挙動は変えない）。`piParse()` はそれを呼んで従来どおり画面に出す。

```js
async function inboxApply(block, links, item){
  const r = piParseText(block);
  if(r.error) return {ok:false, summary:r.error};
  // PJ の決め方：links.projectId があればそれを最優先 → 無ければ r.pjName で候補検索（既存ロジック）
  let p = links.projectId ? proj(links.projectId) : null;
  if(!p){
    const cands = /* piParse と同じ部分一致 */;
    if(cands.length===1) p = cands[0];
    else if(cands.length===0) return {ok:false, summary:'該当するPJが見つかりません：'+r.pjName};
    else return {ok:false, summary:'複数のPJに一致：'+cands.map(x=>x.name).join('／')+'（紐づけ行に PJ の実IDを書いてください）'};
  }
  const res = piApply(p.id, r.items, {silent:true});   // 返り値 {n, coreN, moveIds:[]} を返すように拡張
  inboxAttachLinks(p, res.moveIds, links);              // §2
  return {ok:true, summary:p.name+' に '+res.n+'件'+(res.coreN?'（見立て'+res.coreN+'）':'')};
}
```
- `piApply` は既存どおり。`{silent:true}` のときだけ status 表示・toast・textarea クリアをしない
- 曖昧一致（複数PJ）は保留にして人に戻す（共通部品が保留に残し、Task OS HOME に理由が出る）

## 2. 紐づけ（`links`）の保存
- 取り込みで作られた**ムーブ**（`moves[]` の要素）に `links` を付ける（`strategyGoalId`／`personIds`／`personNames`／`questionId`。`projectId` はPJ自身なので付けない）
- 見立て更新で作られた「見立て更新」ムーブにも同じ `links`
- `personNames` だけのとき：`hitomemo_profiles_v1` を読んで名前の正規化一致が1つだけなら `personIds` を補う（書かない）
- 「取り込む」画面からの手貼りでも、本文の「紐づけ：」行を `inboxParseLinks` で拾って同じく付ける

## 3. PJ に足す項目（4つ・すべて任意・既定は空）

| 項目 | フィールド | 置き場（画面） | 中身 |
|---|---|---|---|
| 戦略目標 | `strategyGoalId`（文字列・`S01`〜） | 詳細の「核」の上、PJ名の右に薄いチップ `S03 ③JSS承継税制`。編集はヘッダーの「✏ 編集」のメタ編集に**セレクト1つ**（空／S01〜S05。表示は番号＋名前） | 対応表は定数 `STRATEGY_GOALS`（Reflect 依頼書と同じ内容）。空＝戦略目標に属さないPJ（例：ゆみさんのPJ）で正常。1つの S-ID に複数PJ・0件も可 |
| Reflect の問い | `reflectQuestionId`（文字列） | 核3行の「現在の問い」の右に小さく `◇ Reflect の問い` のチップ（あるときだけ）。編集はメタ編集に**テキスト1つ**（問いの実ID） | `reflectOS_v1.questions` を読めて id が一致すれば、チップのツールチップに問いの題名を出す。PJ固有の問い（`question` 本文）は今までどおり。両方あってよい |
| 関係者 | `stakeholderIds`（配列・ヒトメモの実ID） | 分岐（`forks[].stakeholders`）は既存の文字列のまま。PJ本体の関係者として、メタ編集に**「関係者（ヒトメモ）」の名前入力＋候補**（`hitomemo_profiles_v1` から名前で絞り込み・最大5件表示・選ぶと id を保存） | 詳細に `👤 父・前田さん` の1行（id→名前はヒトメモから引く。引けなければ id を出さず非表示） |
| 答え合わせする印 | ムーブ（`kind==='次の一手'`）に `answerCheck: true` | 「次の一手」ムーブの行に小さなトグル `⚖ 答え合わせ`（既定オフ。押すと `answerCheck:true`、もう一度で解除）。クイック追加の種類ボタンには**足さない**（既定オフを守る） | 予測帳（VISION見直し担当）へ流す対象の印。**印が付いたものだけ**が対象。PROJECT-IMPORT に `答え合わせ: する` の行があれば、その直前の「次の一手」ムーブに付ける（担当が付けられるように） |

決定ムーブの「予測を付ける」導線：**今回は作らない**。予測は VISION見直し担当のチャットで本人が声かけ「予測」で行い、予測帳に書く運用が決まっており、Project 側に入力欄を作ると二重になるため。PROJECT-IMPORT に `予測: …` の行が来たら、決定ムーブの `text` にはせず、`prediction` として同じムーブに保存するだけ（表示は「決定」行の下に薄く1行）。

## 4. 壁打ちコンテキスト・共有エクスポート
- 壁打ちコンテキスト（単体400字）の先頭行に `戦略目標：S03 ③JSS承継税制`（あるとき）を足す。無ければ行ごと出さない。字数上限は維持
- 共有用エクスポートには `strategyGoalId`／`stakeholderIds`／`reflectQuestionId` を**含めない**（内輪メモ扱い）

## 5. 変えないこと
- PROJECT-IMPORT の既存ラベルの意味、`piApply` の置換・履歴ロジック、`pushMove` の形
- `forks[].stakeholders`（文字列）
- `phaseLabel`、見立て4項目、HOME カード
- 他OSのキーへの書き込み（`hitomemo_profiles_v1`・`reflectOS_v1` は読むだけ）

## 6. 受入条件（playwright）
1. `import_inbox_v1` に `targetOS:'project'`・`links.projectId` にあるPJの id・`block` に PROJECT-IMPORT（決定1・次の一手1・`答え合わせ: する`・センターピン置換）＋紐づけ行（S03／人：父）→ Project を単体で開くとムーブ3件（決定・次の一手・見立て更新）が増え、各ムーブに `links.strategyGoalId:'S03'`・`personNames:['父']`、次の一手ムーブに `answerCheck:true`。`nextMove`・`centerPin` が更新。done に入り、再読み込みで二重にならない
2. `links.projectId` 無し・`PJ: JSS承継` のように部分一致1件 → 取り込める。部分一致が複数 → `ok:false`・保留・理由に候補名。0件 → `ok:false`
3. Task OS から `#frame-project` 経由で合図 → ダイアログなしで処理され、HOME に「{PJ名} に 3件」
4. メタ編集で戦略目標 S03 を選ぶ → `strategyGoalId:'S03'` が保存され、詳細にチップ。空に戻せる。壁打ちコンテキストの先頭に戦略目標行が出て400字以内
5. 関係者の名前入力で「父」と打つ → ヒトメモから候補が出て選ぶと `stakeholderIds` に id。詳細に `👤 父`。ヒトメモに無い名前は保存されない（`forks[].stakeholders` の文字列は従来どおり自由入力）
6. 次の一手ムーブの `⚖ 答え合わせ` トグル → `answerCheck` が true/false で切り替わる。他のムーブ種類には出ない。クイック追加の既定はオフ
7. PROJECT-IMPORT に `予測: 〜` → 直前の決定ムーブに `prediction` が入り、決定行の下に薄く表示。決定行が無い `予測:` は無視
8. 既存データ（`pos_v4`）が改修前後で変わらない。共有エクスポートに新項目が出ない
9. 375px で崩れない・44px・コンソールエラー 0・構文検証 OK・SW 版上げ

## 7. コミット
「project-os: 受信箱（import-inbox）の受け口を追加（共通部品 v1・piParse を解析関数 piParseText に分離・links.projectId 優先・曖昧一致は保留）。ムーブに紐づけ links を保存。PJ に戦略目標 S-ID（セレクト）・Reflect問いID・関係者ヒトメモID（名前候補から選択）を追加、『次の一手』ムーブに答え合わせ印（既定オフ・IMPORT の『答え合わせ: する』対応）、決定ムーブに prediction（IMPORT のみ）。壁打ちコンテキスト先頭に戦略目標行」

## 8. 報告
変更箇所／`piParseText`・`piApply` の返り値の変更／`STRATEGY_GOALS` 定数の場所（Reflect と同じ内容であること）／受入条件9項目／実装を止める場合のみ質問を1つ。
