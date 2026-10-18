# Claude Code 実装依頼書：Lectica実験の実施回数を「ログから導出」して見える化（探求ボードのR系自動反映を含む）

作成日：2026-10-18
対象：`reflect-os/index.html`（主）、`launcher/index.html`・`shot-task-os/index.html`（表示1行ずつ）
土台：main HEAD（2026-10-18 時点）。作業前に `git pull`。

---

## 背景（なぜ）

- Lectica の実践ログは `lectica_experiment_logs_v1`（localStorage・全OS共有）に溜まっている。これが実施回数の**唯一の正本**
- Reflect OS の Lectica 一覧カードには「実施N回」が出るが（`lxCard` が logs から数えている）、**それ以外の場所からは回数が見えない**：ランチャー今日タブの「今日の実験」カード、Shot OS の Lectica Shot 詳細、Task OS
- 探求ボードの実験（R001〜R003＝`rid` を持つもの）の「実践N回・最終 m/d」は、**Reflect の「⬇ 取り込む」で Lectica ログを貼ったときだけ** `practiceCount` を +1 する作り（`lxImportSave`）。手入力フォーム（`lxSaveLog`）からの R系ログや、他の経路で入ったログは反映されない。そのため R001〜R003 が7月から動いていないように見える
- `rid` が空の96本は Cowork の出題対象外なので**空で正しい**。埋めない

## 方針

**実施回数は保存せず、毎回ログから数える**（導出値）。これで「取り込んだときだけ増える」「二重に増える」「手入力は増えない」の3つが同時に消える。

数え方（全OS共通の関数として同じロジックを書く）：
```
count(expId)   = logs のうち experimentId === expId の件数
related(expId) = logs のうち relatedExperimentId === expId の件数
last(expId)    = 上記いずれかに該当するログの date の最大値
```
- `expId` の比較は大文字小文字を無視（R001／r001）
- `logs` が読めない・配列でないときは 0件扱い（表示しない）
- 日付は `YYYY-MM-DD` 文字列比較でよい

---

## 1. Reflect OS（`reflect-os/index.html`）

### 1-1. 探求ボードの R系実験：`practiceCount`／`lastPracticedAt` を導出に切り替える
- 表示箇所（探求ボードのカード `'実践'+x.practiceCount+'回'+…`）で、`x.rid` があるときは **保存値ではなくログから数えた値**を使う：`実践 {count(rid)+related(rid)} 回・最終 {last(rid)}`。0回なら行ごと出さない
- `rid` が無い実験は従来どおり（保存値があれば表示。無ければ非表示）
- `lxImportSave` 内の「R系連動」ブロック（`x.practiceCount=(x.practiceCount||0)+1` …）は**撤去**し、代わりに `tkSave('experiments',x)` で `updatedAt` だけ進める（問いの `updatedAt` 連動は残す）。保存値 `practiceCount`／`lastPracticedAt` は消さない（他所で読んでいる可能性があるため残置。ただし以後は更新しない）
- `lxSaveLog`（手入力フォーム）で R系の `experimentId` を保存したときも、同じく該当実験の `updatedAt` を進める

### 1-2. Lectica 一覧：回数の見え方を少し揃える
- `lxCard` の「実施N回（＋関連M）」チップはそのまま。横に **最終実施日**（`最終 m/d`）を薄く添える。0回なら従来どおり非表示
- 一覧の並び替えに **「実施回数順」** を1つ足す（既存の並び替えUIがあればそこに、無ければ見出し右の小さなセレクト。既定は変えない）

### 1-3. やらないこと
- `rid` の自動付与ロジック（`tkAutoAssignRids`）は触らない
- 96本の `rid` を埋める処理は作らない
- 催促・件数バッジ・「0回」表示は出さない

---

## 2. ランチャー 今日タブの「今日の実験」カード（`launcher/index.html` `renderLectinCard`）

- お題の行の下に1行：**「これまで N回（最終 m/d）」**。N＝`count(experimentId)+related(experimentId)`。0回なら出さない
- 関連実験（`relatedExperimentId`）があれば、その行にも同じ形で添える（0回なら出さない）
- 文字は本文より小さく・薄く（既存 `.lx-k` と同系）。カード高さが1行分増える以外、レイアウトは変えない

## 3. Shot OS の Lectica Shot 詳細（`shot-task-os/index.html` `renderLecticaDetail`）

- 「お題」行の末尾、または直下に **「これまで N回（最終 m/d）」**。`lecticaDetail.experimentId`（無ければ memo から拾った実験ID）で数える。0回なら出さない
- `lecticaDetail` が無い旧Shotでも、memo から実験IDが取れれば出す

## 4. Task OS（`task-os/index.html`）

- 変更なし（Lectica Shot のカードは Shot OS の表示を使っているため）。もし Task OS 側に独自の Lectica カード描画があれば、Shot OS と同じ1行を足す

---

## 5. 検証（playwright・実データ相当のログを入れて）

1. `lectica_experiment_logs_v1` に L042×3件（うち1件は `relatedExperimentId:'R001'`）、R001×2件（`experimentId:'R001'`）、日付をばらして投入
2. Reflect Lectica 一覧：L042 のカードに「実施3回・最終 {最大日}」。R001 の探求ボードカードに「実践3回（2＋関連1）・最終 {最大日}」が、**取り込み操作をせずに**出る
3. Reflect「⬇ 取り込む」で R001 のログを1件追加 → 探求ボードが4回になる。同じログをもう一度貼っても（ログ側で重複しない限り）回数は変わらない。`practiceCount` の保存値は増えていない
4. Reflect 手入力フォームで R001 のログを1件保存 → 探求ボードが5回になる
5. ランチャー今日タブ：`aix_draft_latest` の `lectica_daily_practice.experimentId='L042'` を置く → 「これまで3回（最終 m/d）」が出る。ログ0件の実験IDなら行が出ない
6. Shot OS：`lecticaDetail.experimentId='L042'` の Shot を開く → 同じ1行。旧形式（memo のみ）でも出る
7. `lectica_experiment_logs_v1` が壊れた JSON のとき、どの画面もエラーにならず行が出ないだけ
8. 探求ボードで `rid` の無い実験の表示が変わっていない。96本の `rid` が空のまま
9. 375px幅で崩れない・コンソールエラー0・構文チェックOK

## 6. コミット

「lectica: 実施回数をログ（lectica_experiment_logs_v1）から導出に統一。探求ボードR系の実践回数は取り込み時の+1をやめログから数える（手入力・他経路のログも反映）。ランチャー今日タブとShot OSのLectica詳細に『これまでN回（最終 m/d）』を追加（0回は非表示）」

## 7. 報告

変更ファイル3つ／導出関数の名前と置き場所（各ファイルに同ロジックで複製）／`lxImportSave` から撤去した箇所／検証9項目の結果。実装を止める場合のみ質問を1つ。
