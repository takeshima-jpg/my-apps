> ✅ 実装済み 2026-07-12 ・ 8bf0153（安全パースjGet/bGet＋restore対称化。aix_draft_latestはcollect対象外＝別系統のため変更なし）

# Claude Code 緊急修正依頼書：Task OS 同期エラー（週次レビューのJSON.parse失敗）

genId修正後、今度は別の同期エラーが発生。「同期エラー（再試行）」ボタンが出る。

## エラー
```
gdAutoSync error SyntaxError: Unexpected token '�', "📣 週次レビュー |"... is not valid JSON
    at JSON.parse (<anonymous>)
    at collectAllOSData (index.html:710:38)
    at collectAllOSDataWithReflect (index.html:687:16)
    at gdAutoSync (index.html:2373:28)
```

## 原因
- collectAllOSData（全OSバックアップ収集）が、localStorage の週次/月次レビューデータを `JSON.parse` している。
- しかし週次・月次レビュー（`aix_review_weekly` / `aix_review_monthly`）は **markdown文字列**で保存される
  （2026-07に週次もmarkdown移行済み）。生markdown「📣 週次レビュー｜…」をJSON.parseするので SyntaxError。
- 今日（日曜）の週次レビューが生成され aix_review_weekly に入って初めて発火した潜在バグ。
- 例外で collectAllOSData が失敗 → gdAutoSync（同期・バックアップ保存）が丸ごと止まる。

## 調査ポイント
- index.html:710 付近の collectAllOSData で、どのキーを JSON.parse しているか確認。
  特に aix_review_weekly / aix_review_monthly / aix_draft_latest（これも今はmarkdown文字列）。
- これらは「オブジェクトの場合もあれば markdown文字列の場合もある」。日次briefで既に採用済みの
  「オブジェクト/文字列/JSON文字列の3形式対応」（1dayのgetAixDraft、brief-viewerのtoMarkdown等）と同じ考え方で扱う。

## 修正
- collectAllOSData 内で aix_draft_latest / aix_review_weekly / aix_review_monthly を収集する際、
  **JSON.parse を安全化**する：
  ```
  安全パース(raw):
    raw が null/空 → null
    try JSON.parse(raw) して成功すれば その値（オブジェクトでも文字列でも）
    失敗すれば raw（生markdown文字列）をそのまま採用
  ```
  → markdown文字列はそのまま文字列として、オブジェクトはオブジェクトとしてバックアップに入る。
- 併せて、他に localStorage値を無防備に JSON.parse している箇所が collectAllOSData 内に無いか確認し、
  同様の潜在クラッシュがあれば安全パースに統一する。
- restoreAllOSData（復元側）も対称であること（文字列/オブジェクト両対応で書き戻せる）を確認。

## 二次防御
- collectAllOSData 全体、または各キーの収集を try/catch で包み、**1キーのparse失敗が
  バックアップ全体を止めない**ようにする（そのキーは null/生値でスキップし、他OSデータは収集を続行）。
  同期・バックアップは「一部が欠けても止めずに残す」方が安全。

## 検証
- node --check（pre-commit）
- aix_review_weekly に生markdown（「📣 週次レビュー｜…」）が入った状態で gdAutoSync が
  SyntaxErrorなく完了し、バックアップに週次markdownが文字列として含まれること
- aix_draft_latest（markdown）・aix_review_monthly でも同様にエラーが出ないこと
- 「同期エラー（再試行）」表示が消え、GDrive同期・全OSバックアップ保存が成功すること
- restoreで週次/月次/日次briefが正しく書き戻ること（往復確認）

## コミット
「task-os: collectAllOSDataが週次/月次/日次briefのmarkdown文字列をJSON.parseして同期が落ちるバグを修正。
安全パース（オブジェクト/文字列両対応）＋キー単位try/catchで一部失敗が全体を止めないよう防御」
