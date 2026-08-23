# Claude Code 実装依頼書：Task OSのルーチン完了を Routine OS の次回日計算に揃える（サイクルずれの根治）

作成日：2026-08-23
対象：`task-os/index.html` の `completeRt()`（1328行付近）、参照元：`routine-os/index.html`
作業前に必ず `git pull`。

## 問題（実機で確認・竹嶋さん報告）

Task OS HOME からルーチンを✓完了すると、次回予定日が**今日＋addDays固定**で計算される：

```js
t.nextDate = addD(TODAY, parseInt(t.addDays)||7);   // 1331行
```

これは Routine OS 本家の `calcNextRoutineDate()` と別ロジックで、以下を全て無視している：
- **加算基準**（from_next=前回予定日から／from_last=最終実施日から／from_ms・from_me・from_ys・fixed）
- **加算タイプ**（カレンダー日／月／年のサイクル）
- **キャッチアップ**（過去日になる場合は未来日になるまで繰り返し加算）

実害：土曜サイクルの「タスク見直し」を期日切れ後の日曜に Task OS から完了 → 次回が日曜起点にずれた。
期日切れのたびに曜日がずれ続ける。8/23引継ぎカードの残課題「completeRt は addDays 固定」の実害化。

## 望む挙動（竹嶋さん確認済み）

**ルーチンごとの「加算基準」設定を尊重する。**
- `from_next`（前回予定日から加算）のルーチン：期日切れ後に完了しても、**旧予定日を基準に**サイクル加算。
  過去になる場合は未来日になるまで繰り返し加算（＝曜日・周期が守られる）
- `from_last`（最終実施日から加算）のルーチン：完了日基準が**正しい**挙動なのでそのまま
  （「やってからN日」型。常に予定日基準へ倒すのではない点に注意）
- Routine OS から完了した場合と**完全に同じ結果**になること

## 実装方針：Routine OS の計算ロジックを移植し、同期コメント契約を張る

Routine OS の以下の関数群を Task OS に**そのまま移植**する（改変しない）：
`normalizeCycle`(517)／`parseLocalDate`(872)／`formatLocalDate`(882)／`getTodayLocalString`(888)／
`addDaysLocal`(891)／`addMonthsLocal`(895)／`addYearsLocal`(902)／`getRoutineInterval`(904)／
`calcNextRoutineDate`(912)

- Task OS 側に同名関数が既にある場合は名前衝突を確認し、衝突するなら `rt` プレフィックスを付けて一式改名
  （routine-os 側は変更しない）
- **両ファイルの関数ブロック先頭に同期コメントを必ず書く**：
  `// ※routine-os/index.html の同名関数と同一実装。変更時は両方を同時に更新すること（brief-viewer/1day の markdownToHtml と同じ契約）`

### completeRt の書き換え

```js
function completeRt(rawId){
  const a=getRt(), t=a.find(x=>String(x.id)===String(rawId)); if(!t) return;
  const prev = t.nextDate || TODAY;                       // 旧予定日（期日切れならその過去日）
  const nextDate = calcNextRoutineDate(t, prev);          // 移植した本家ロジック
  if(!nextDate){ toast('⚠ 次回予定日を計算できません（Routine OSで設定を確認）'); return; }
  t.lastDone=TODAY; t.lastDate=prev; t.updatedAt=now(); t.nextDate=nextDate; t.status='';
  saveRt(a); addRtLog(t,'完了',prev,t.nextDate); toast(`✓ 完了 → 次回 ${fmtDate(t.nextDate)}`); refresh();
}
```

- `calcNextRoutineDate` が null（サイクル設定不備）の場合は**上書きせず**トーストで知らせて中断
  （現行の addDays フォールバックで誤った日付を書くより、書かない方が安全）
- `postponeRt`（翌日へ+1日）は**現状維持**。延期は周期計算ではない
- `addRtLog` の `newNextDate` に正しい値が入ること（週次ファクト・Routine OS履歴の整合に影響）

## 変更しないこと【厳守】
- routine-os/index.html は**1バイトも変更しない**（コメント追記のみ可）
- completeSh／postponeRt／postponeSh
- addRtLog のログ形式
- 5094d34 で入った completedAt・ログ追記の挙動

## 検証
- 構文検証（node --check）
- from_next・週次・旧nextDate=昨日（土曜想定）のルーチンを今日完了 → 次回が**来週の同じ曜日**になる
  （今日＋7ではない）
- from_next・旧nextDateが2週間以上前 → キャッチアップで未来の直近周期日になる（過去日にならない）
- from_last のルーチンを完了 → 完了日基準で加算される（従来挙動＝本家と同じ）
- 月次サイクル（from_ms等）→ Routine OS で完了した場合と同一の次回日になる（両OSで同一タスクを比較）
- サイクル設定不備のタスク → nextDate が変更されず、警告トーストが出る
- addRtLog の previousNextDate／newNextDate が正しい
- リロード後維持・コンソールエラーなし

## コミット
「task-os: completeRtの次回日計算をRoutine OSのcalcNextRoutineDateに統一（加算基準・サイクル・キャッチアップを尊重）。期日切れ後の完了でも周期の曜日が守られるように。計算不能時は上書きせず警告（両OSの同期コメント契約を追加）」

## 報告
移植した関数一覧（改名の有無）／同期コメントの位置／検証結果（特に from_next 土曜→日曜完了ケース）。
実装を止める場合のみ質問を1つ。
