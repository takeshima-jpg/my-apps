# Claude Code 実装依頼書：Task OSに「重点の問い」を表示＋Reflect実験（R系）の提案受け入れ

作成日：2026-08-18
対象：`task-os/index.html`
前提：依頼書A（reflect-nav-consolidation）の④で `reflect_focus_v1` ミラーが入っていること。**Aを先に実装すること。**
作業前に `git pull`。

## 背景（竹嶋さんの要望）
- 「重点の問い」と実験中の実験を**忘れてしまう**ので、毎日見るTask OSに表示したい
- 毎日のBriefの✦枠（Lectica×Reflect統合枠）で、Lecticaマスタ実験だけでなく**Reflect側の実験（R系）も実行できる**ようにしたい

## ① HOMEに「重点の問い」カードを表示する（閲覧専用）

localStorageの `reflect_focus_v1`（依頼書Aで定義）を読み、HOMEに静かなカードを1枚描く。

- 位置：「PJの現在地」の直後（既存の気づきカードの前後は実装judgeでよいが、期限超過バナーより上には置かない）
- 内容：
  - 各重点の問い（最大3）を1行ずつ。その下に紐づく実験中の実験をインデントで1行ずつ（「〜してみる」＋使う場面があれば括弧書き）
  - `unlinkedExperiments` があれば「（問い未設定）」として同様に
- **閲覧専用**。ボタン・チェック・入力は一切置かない。カードクリックでReflect OS（`../reflect-os/`）を開くのは可
- `reflect_focus_v1` が無い／全て空のときは**カードごと出さない**（空カード・プレースホルダ禁止＝催促しない）
- 既存のHOME描画（PJの現在地・今日やること・週次等）には一切干渉しない

## ② 参謀提案のR系実験（Reflect実験）を受け入れる

現状 `autoGenLecticaShot()` は提案IDを `lectica_experiments_master_v1` と突き合わせており（`byId(pid)` → `usable(pe)`）、
**マスタに無いID（Reflect探求ボードの実験）は無条件で落ちる**。パッチS（統合棚卸し）でBriefがR系を出せるようになったため、ここを通す。

修正（1657行〜の提案判定部）：

- `pid` がマスタに**ある**場合：従来どおり `usable(pe)` を通す（completed/skippedのL実験は再出題しない）
- `pid` がマスタに**ない**場合：**pending自体を信頼して採用する**
  - 条件：日付一致（既存判定のまま）かつ `pending.shotTask` または `selectedExperimentTitle` がある（タイトルが作れる）
  - `sanboExp` が取れないので、Shot生成・差し替えに使うタイトル/メモは `pending.shotTask` を正とし、
    memoの実験ID行は `pid` をそのまま書く（例：`実験ID：R001`）
  - マスタ側の `status='active'` 昇格処理（1697行）はマスタに無いIDでは**スキップ**（エラーにしない）
- 選定責任はCowork側にある原則は不変：R系の妥当性（活動中か等）はTask OSでは判定しない
- `addLecticaShot()`（launcher）側も同じ考え方で、R系IDの提案が来た場合に落ちないことを確認する（カテゴリ基準の二重防止はそのまま効くはず）

## 検証
- 構文検証（node --check）
- `reflect_focus_v1` あり → HOMEに重点カードが出る／無し・空 → 何も出ない・エラーなし
- 重点カードに操作要素が無い・既存HOMEセクションの表示が変わらない
- pendingのIDがL系（マスタあり・usable）→ 従来どおり採用
- pendingのIDがL系（completed）→ 従来どおり不採用
- pendingのIDがR系（マスタなし）＋shotTaskあり → **採用され、memoに「実験ID：R001」が入る**
- R系採用時にマスタ更新処理でエラーが出ない
- 既存ランダムShot（todo）がある状態でR系提案 → 置き換わり件数1件のまま（冪等）
- リロード後維持・コンソールエラーなし

## コミット
「task-os: HOMEにReflectの重点の問い/実験中を閲覧専用カードで表示（reflect_focus_v1参照・空なら非表示）。参謀提案のR系実験（Lecticaマスタ外）を受け入れ、Brief統合枠からReflect実験を実行可能に」

## 報告
変更箇所／R系判定の実装方法／launcher側の確認結果／検証結果。実装を止める場合のみ質問を1つ。
