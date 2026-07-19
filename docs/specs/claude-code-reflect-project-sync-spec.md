# Claude Code 実装依頼書：Reflect OSのProject同期をv2.2に追従させる

> ✅ 実装済み 2026-07-19 ・ `99dfb66`
> 実装メモ：現用テーマストアは reflectOS_v1（localStorage）と確認（idbはレガシー・不変）。
> テーマの実フィールド名は question/hypothesis ではなく currentState/summary だったため
> スキーマ新設はせずここへ集約。参照用に goal/badFuture/successConditions/nextMove を保持。
> PJ側の「次の一手」は v2.1以降 nextMove（旧 nextAction もフォールバック）。
> 対応PJ削除時は旧実装の「status=完了」をやめ _fromProjectOS=false の手動テーマ化に変更。

作成日：2026-07-18
対象：repoの `reflect-os/index.html`（主）。作業前に `git pull`。
※ Project OS側は変更しない（Reflect側の同期処理と表示のみ）。データ破壊なし。

## 問題（実バックアップで確認済み）
Reflect OSの探求テーマにProject OSの4PJが「タイトルだけ」同期されており、
question も hypothesis も空。一方 Project OS 側は v2.1/v2.2 で各PJに
goal / centerPin / badFuture / successConditions / nextAction を持つように育っている。
＝同期がPJ名の器だけ作り、中身を運んでいない。これを追従させる。

## Project OS の実フィールド（projectOS.projects[] で確認済み・これを正とする）
- `name`：PJ名
- `goal`：ゴール
- `centerPin`：現状のセンターピン（v2.2新設）
- `badFuture`：悪い未来（v2.2新設）
- `successConditions`：成功条件（文字列）
- `nextAction`：次の一手
- `attentionIssue` / `issueMemo`：注意論点・論点メモ（＝「現在の問い」に相当する材料はここ）
- ※ 独立した `question` フィールドは一部PJにしか無い（UI入力分のみ）。question が空なら
  issueMemo → attentionIssue の順でフォールバックして「現在の問い」材料とする。
- `status`（進行中/構想中等）/ `priority`（高/A等）/ `updatedAt`

## Reflect OS 側の現状（要確認）
- テーマは reflectOS(v1) 側に8件、reflectOS_idb 側に13件と二重に存在する。
  **どちらが探求ボードの現用ストアか実コードで確認し、現用側だけを対象にする**
  （Phase 1 で主データは reflectOS_v1＝localStorage と判明済み。idb はレガシーの想定）。
- テーマのスキーマ：title / status / priority / question / hypothesis。

# 変更1：同期でProjectの中身をテーマへ運ぶ
「PJ同期」実行時、Project OS の各PJに対応する探求テーマへ以下をマッピングする：
- テーマ `title` ← PJ `name`（既存どおり・突合キー）
- テーマ `status` ← PJ `status`
- テーマ `priority` ← PJ `priority`
- テーマ `question` ← PJ `question`（空なら issueMemo、それも空なら attentionIssue の先頭要点）
- テーマ `hypothesis` ← PJ `centerPin`（センターピンを仮説として扱う。空なら goal）
- テーマに新フィールドを足してよい場合は、`goal` / `badFuture` / `successConditions` /
  `nextAction` も保持し、テーマ詳細で参照できるようにする（スキーマ拡張が重いなら
  question/hypothesis への集約でよい。実装しやすい方を選び、報告に明記）。

## 同期の上書きルール【重要・手入力を壊さない】
- Project由来テーマ（PJと名前一致）のみ更新対象。純粋な手動テーマ（仲間づくり等）は触らない。
- テーマ側でユーザーが手入力した question/hypothesis がある場合、
  **空でない既存値は上書きしない**（Project値で上書きするのは、テーマ側が空のときだけ）。
  ＝同期は「空欄を埋める」方向。手で書いた探求内容をProjectの値で潰さない。
- 対応PJが削除された場合もテーマは消さない（手動テーマ化して残す）。

# 変更2：テーマ表示にProjectの中身を出す
探求ボードのテーマ表示（またはテーマに紐づく問い一覧の上部）で、
Project由来テーマは goal / centerPin（=hypothesis）/ 現在の問い を読めるようにする。
「タイトルだけの空テーマ」に見えないようにするのが目的。

# 変更3：同期タイミング
- 現行の「PJ同期」ボタンの手動実行を維持（自動同期は追加しない）。
- 同期後、テーマ一覧・件数が即時更新されること。

# 検証
- 構文検証（node --check / esbuild）
- PJ同期実行後、4PJテーマの question/hypothesis が Project の値で埋まる
  （前田さんテーマの hypothesis に centerPin「前田さんの2030年の理想状態を…」が入る等）
- テーマ側に手入力値があるテーマは同期で上書きされない
- 手動テーマ（仲間づくり・挑戦の環境づくり・自分らしい生き方）が無傷
- 現用ストア（v1想定）のみ更新され、レガシー側との不整合が新規発生しない
- リロード後維持・JSONエクスポートに反映・モバイル375pxで崩れない・コンソールエラーなし

# コミット
「reflect-os: Project同期をv2.2フィールド（centerPin/badFuture/successConditions/goal/
nextAction）に追従。PJの中身をテーマのquestion/hypothesisへ空欄補完で運ぶ（手入力は上書きしない）」

# 報告
変更ファイル／現用テーマストアの判定結果（v1かidbか）／マッピングの最終形（テーマにフィールド
拡張したか集約したか）／上書き防止の実装／テスト結果。
実装を止める場合のみ質問を1つ。
