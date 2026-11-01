# Claude Code 実装依頼書：実験のShotを閉じるときに「結果」を1タップで残す（やった／やってない／後でやる）

作成日：2026-11-01（メンテナンス担当。Morning Brief の申し送り「実験のShotを完了にするとき結果を1語で残せるようにする」・本人決定 11/1）
対象：`task-os/index.html`、`shot-task-os/index.html`
土台：main `0044e3c`。作業前に `git pull`。

---

## 背景（なぜ）

- Lectica の実験の結果は壁打ちチャットに「結果」と打って残していたが、10月は場面が来ても結果が残らない日が多かった（10/27〜10/29 の3本は 11/1 に本人が「やらなかった」と返事）。
- 本人は実験のShot（「今日の実験：…」）には触っている（10/27 分は 10/29 に完了、10/28・10/29 分は削除）。戻っている場所＝Shotを閉じる操作に結果を乗せる。
- 11/1 本人決定：答えは3語「やった／やってない／後でやる」。
- 11/2 から参謀が `shotTask.memo` の末尾に `結果：（やった／やってない／後でやる のどれか1語）` を置く（OSを直さなくても、本人がメモを書き換えれば運用できる）。この依頼は、それを1タップにする改善。

## いまの挙動（コードで確認）

- 実験のShot＝`category:'Lectica'`（`lecticaDetail` あり）。Task OS の同期が `daily-tasks.json` の `lectica_daily_practice.shotTask` から作る
- 完了は2か所：Task OS `completeSh`（1538行・Lectica だけ `confirm('この実験を完了にしますか？')`）、Shot Task OS `lecticaComplete`（1285行・同じ confirm）→ `status:'done'`・`completedAt`
- Shot Task OS は期日超過の未完了 Lectica を起動時に自動で `pending`（保留）にする（`lecticaAutoPaused`）
- 削除は Shot Task OS `deleteTask`（2回押し）。消すと何も残らない
- 実施回数は `lectica_experiment_logs_v1`（Lecticaログ）から数える（全OS共通）。Shot の状態は回数に入らない

## 1. 閉じるときの3択（両OS・同じ部品）

- Lectica のShotの「✓ 完了」「完了」を押したとき、今の `confirm` の代わりに**3択の小さなシート**を出す：「やった」「やってない」「後でやる」＋小さく「やめる」
  - 押す回数は今と同じ（✓→確認 が ✓→3択 に変わるだけ）。ボタンは高さ 44px 以上、横並び（375px では縦並び可）
  - モーダルではなく、そのカードの下にその場で開く形が望ましい（Task OS の既存の書き方に合わせる。モーダルしか無理なら簡素なもの）
- 選んだ結果の保存（共通）：
  - `lecticaDetail.result`＝`'done'`／`'not_done'`／`'later'`、`lecticaDetail.resultAt`＝ISO
  - `memo` の `結果：` で始まる行を `結果：やった`（日本語の1語）に書き換える。行が無ければ末尾に足す
- 状態の扱い：
  - **やった** → `status:'done'`・`completedAt`（今と同じ）
  - **やってない** → `status:'done'`・`completedAt`（完了にする・本人決定 11/1）。「やった」との区別は `lecticaDetail.result` と memo の「結果：」行で行う（週次の Shot 完了数に入るので、参謀は Lectica のShotを `result` で分けて数える）
  - **後でやる** → 閉じない。`status` はそのまま、`dueDate` を翌営業日へ（Task OS の `postponeSh` と同じ考え方。土日は飛ばす。祝日は `routineOS_holidays` があれば飛ばす）、`memo` の先頭に `持ち越し：M/D→M/D` を1行足す。`lecticaAutoPaused` は外す
- 同じShotで結果を選び直したら、最後の選択で上書き（`resultAt` も更新）
- 「未着手に戻す」「戻す」で `done` から戻したときは、`lecticaDetail.result` と `memo` の「結果：」行は**消さない**（記録として残す）

## 2. 削除のとき

- Lectica のShotの削除（Shot Task OS `deleteTask`）は、2回目の押下の前に同じ3択を出し、「やった／やってない」を選べばそれを残して**削除ではなく**上の状態にする。「結果なしで消す」を選んだときだけ今までどおり消す
- Task OS 側に Shot の削除が無ければ対応不要

## 3. 期日超過の自動保留との関係

- 自動保留（`lecticaAutoPaused`）は結果を書かない（`result` 無し＝本人が選んでいない、として参謀が読む）。今の挙動は変えない

## 4. やらないこと

- Lecticaログ（`lectica_experiment_logs_v1`）へ自動で書き足すこと（申し送りの案B）。実施回数がログから数えられているため、Shot から足すと壁打ち・Reflect の取り込みと二重になり回数が狂う。結果はShotに残し、参謀が読む
- 「やった」のときの一言欄（案B）は今回入れない（入れるなら次回、任意・30字・`lecticaDetail.note`）
- Lectica 以外のShotの完了操作

## 5. 受入条件（playwright。Task OS HOME と Shot Task OS の両方）

1. Lectica のShotで ✓ → 3択が出る。「やった」→ done・completedAt・`lecticaDetail.result:'done'`・`resultAt`・memo に `結果：やった`
2. 「やってない」→ done・completedAt・`result:'not_done'`・memo `結果：やってない`。Task OS の今日の一覧から消える
3. 「後でやる」→ 状態は変わらず、dueDate が翌営業日（金曜なら月曜）・memo 先頭に `持ち越し：…`・`result:'later'`。翌日のHOMEに出る
4. 「やめる」→ 何も変わらない
5. memo に「結果：」行がある場合は書き換え、無い場合は末尾に足す（どちらも1行だけ）
6. Shot Task OS の削除で3択 →「やった」を選ぶと消えずに done、「結果なしで消す」で消える
7. Lectica 以外のShotは今までどおり即完了
8. バックアップ（myapps-all-backup）の `shotTaskOS` に `lecticaDetail.result`・`resultAt` がそのまま出る
9. 375px・ボタン 44px 以上・コンソールエラー0・構文検証OK・task-os の BUILD_VER を当日に・両OSの SW 版上げ

## 6. コミット

「task-os/shot-task-os: 実験のShotを閉じるときに結果3択（やった／やってない／後でやる）を出し lecticaDetail.result と memo の『結果：』行に残す。やった・やってない＝完了（結果で区別）、後でやる＝翌営業日へ持ち越し。削除時も結果を選べる。壁打ちに戻らず結果が残らなかったため（11/1 本人決定）」

## 7. 報告

変更箇所（両OSの関数名）／受入条件9項目／実装を止める場合のみ質問を1つ。配置後、メンテナンス担当が記録の地図に `lecticaDetail.result` を足し、Morning Brief へ「直りました」を返す。
