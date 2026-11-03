# Claude Code 実装依頼書：Reflect から PJ と戦略目標の紐づけを外す（在り方と案件を分ける）

作成日：2026-11-03（メンテナンス担当。本人決定 11/3：B）
対象：`reflect-os/index.html`、`CLAUDE.md`
土台：main `ae4d23e`。作業前に `git pull`。

---

## 背景（なぜ）

- 11/1〜11/3 のリフレクト棚卸しで、本人と「**Reflect＝自分がどう在るか（在り方）、Project＝案件をどう進めるか**」と分けると決めた。PJ をテーマに写すのは `3b52ffc` でやめた
- ところが Reflect の問い・実験には、今も PJ と戦略目標の紐づけ（`links.projectId`／`projectName`／`strategyGoalId`）が残っている（11/3 朝：問い7本・実験3本。一部は `3b52ffc` の「外したテーマ」の移行で補ったもの）。例：重点の問い「相手の人生と会社の未来をどう接続し、人生応援と経営責任を両立するか？」（`mrra2m5n4b8q9cml89u`）に「S05 ⑤仲間づくり／PJ チーム竹嶋づくり」
- 本人決定（11/3・B）：**Reflect からは PJ の紐づけを全部外す。案件と在り方のつながりは、PJ 側の紐づけ行「問い：」（Project のムーブの `links.questionId`＝PJ から問いを指す）だけで持つ**
- 戦略目標（S-ID）も外す（戦略目標の実体は Project の PJ＝案件の軸のため）。**人の紐づけ（`personIds`／`personNames`）と問いのつなぎ（実験の `questionId`）は残す**
- Reflect の紐づけを OS が使っているのは画面のチップだけ（並べ替え・上限・R番号・`reflect_focus_v1`・バックアップ要約には使っていない）。外しても OS の動きは変わらない

## 1. 今ある紐づけを外す（起動時1回・冪等）

- 対象：IndexedDB の `questions`・`experiments`・`logs`・`themes`・`principles` と、Lectica の実践ログ（`lectica_experiment_logs_v1`）。どの状態（合流済み・保管・下書き・外したテーマを含む）も対象
- `links` から `projectId`・`projectName`・`strategyGoalId`（と `strategyGoalName` などその仲間があれば）を消す。残りが空なら `links` ごと消す。`personIds`・`personNames`・`questionId` などはそのまま
- 外す前に、**問い・実験・テーマだけ**、記録（`notes`）に1行残す：`{date:'2026-11-03', kind:'旧 紐づけ', text:'S05 ⑤仲間づくり／PJ チーム竹嶋づくり（在り方と案件を分けるため外した）', src:'移行'}`（今の PJ 名で。振り返りログと Lectica ログには残さない）
- 外したテーマ（`detached:true`）の `projectId`（テーマ自体の欄）は、どの PJ の写しだったかの記録なので**残す**（`links` ではない）
- 退避キー `reflect_backup_unlink_20261103`（変える前の該当レコードの `id` と `links` だけ）・フラグ `reflect_unlink_20261103_done`。トースト1回「PJ・戦略目標の紐づけを n件外しました（在り方と案件を分けるため）」
- `reflect_detach_20261102`（外したテーマの問い・実験に `links.projectId` を補う移行）が、フラグの無い環境（古いバックアップの復元など）でこの移行より後に走って PJ を付け直さないこと。順番を「detach → unlink」にし、detach が補う処理は外してよい

## 2. これから PJ・戦略目標を付けない

- 受信箱の取り込み（`inboxAttachLinks`）・本文の「紐づけ：」行（1853行付近）・REFLECT-UPDATE・【振り返り】・Lectica の結果ブロックのどれで入ってきても、Reflect のレコードには **PJ と戦略目標を付けない**（人だけ付ける）。`rfKeepPj` は不要になる
- 受信箱の summary に、PJ・戦略目標が書かれていたときだけ1回「紐づけの PJ・戦略目標は Reflect には付けません（PJ 側の『問い：』で持ちます）」。取り込みそのものは通す（保留にしない）
- 受信箱の記録（`importInbox.log` の `links`）は Task OS 側の写しなので今のまま

## 3. 画面

- 紐づけのチップ（`rfLinkChips`）は人だけを出す（PJ・S-ID のチップは出なくなる）
- 移行後、問い・実験の詳細の記録に「旧 紐づけ」の行が出る（今の記録の表示のまま。特別な表示は要らない）

## 4. 変えないこと

- Project OS（ムーブの `links.questionId`＝PJ から問いを指す紐づけはそのまま）
- 探求ボードの上限・R番号・統合・保管・テーマの VISION のつなぎ（`visionLink`）
- `reflect_focus_v1`・バックアップ要約の形

## 5. CLAUDE.md

- データ契約の Reflect の `links` に「PJ・戦略目標は持たない（2026-11-03）。案件とのつながりは Project のムーブの `links.questionId`」を追記

## 6. 受入条件（playwright・11/3 のバックアップ相当）

1. 起動で、問い・実験・ログ・テーマ・Lectica ログの `links` から PJ と S-ID が消える。人の紐づけと実験の `questionId` は残る。問い・実験・テーマの記録に「旧 紐づけ」1行。退避1つ・再読み込みで二度走らない
2. フラグを消して `reflect_detach_20261102` も未実行の状態から起動 → detach の後に unlink が走り、PJ が残らない
3. 受信箱で `紐づけ：S03 ③JSS承継税制／PJ：wqt4wwbrizm JSS承継親孝行プロジェクト／👤 …` 付きの REFLECT-UPDATE・`■ 問い 新規`・【振り返り】を入れる → 中身は入り、PJ・S-ID は付かず人だけ付く。summary に1行
4. 問い・実験のカードに PJ・S-ID のチップが出ない。375px・コンソールエラー0
5. 「直前の更新を元に戻す」は従来どおり。構文検証・pre-commit 通過・SW 版上げ

## 7. コミット

「reflect-os: Reflect の問い・実験・ログ・テーマ・Lectica ログから PJ と戦略目標の紐づけを外す（起動時1回・旧紐づけは記録に1行・退避あり）。これからも付けない（人の紐づけは残す）。在り方（Reflect）と案件（Project）を分け、つながりは PJ 側の『問い：』で持つため（11/3 本人決定）」

## 8. 報告

変更箇所／外した件数（問い・実験・ログ・テーマ・Lectica ログ別）／**Reflect 側にだけあった PJ と問いのつながりの一覧**（問いの題名・実ID と、付いていた PJ 名。Project のムーブに同じ問いIDの紐づけが無いもの）／受入5項目。実装を止める場合のみ質問を1つ。
