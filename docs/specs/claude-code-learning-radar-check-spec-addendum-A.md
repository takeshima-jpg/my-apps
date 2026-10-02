# 追補A：学びレーダー Phase 3-A（判定の照合キーと「打合せ」区分）

作成：2026-10-03 設計チャット／対象：`learning-radar/index.html`（Phase 3-A 実装分への追補）
理由：初回の学びチェックで、①バックアップ未同期だと `eventId` が取れない、②通常の打合せとの重複を表す区分が無い、の2点が判明した。

## A-1. 判定の照合キー（eventId 依存をやめる）
`learning-check.json` の各判定に `url` / `startDate` / `title` が入る（Cowork側で追加）。OS側の照合は次の順：
1. `eventId` が存在し、OSの `events[].id` に一致 → それ
2. 無ければ `normalizeUrl(url) + startDate` が一致する予定（取込の重複判定と同じ正規化・同じ関数を使う）
3. 無ければ `normalizeTitle(title) + startDate` が一致する予定
4. どれにも当たらなければ捨てる（従来どおり無視）

同じ予定に複数の判定が当たった場合は `generatedAt` が新しい方。保存先は従来どおり `settings.checks[eventId]`（照合後にOSのidで保存する）。

## A-2. 区分の追加
`verdict` に `meeting` を追加（7値）。`label` は「重複：打合せ（{予定名}）」。表示色は `dinner / away / dinnerRule` と同じ（文字色 `--tx`）。赤は使わない。
未知の `verdict` が来た場合は、`label` をそのまま `--tx2` で表示する（捨てない。Cowork側の追加に画面が追随できるように）。

## A-3. 受入条件（追加分）
1. `eventId` 無し・`url`＋`startDate` のみの判定が、取込済みの予定に当たる
2. URLが無い予定は `title`＋`startDate` で当たる
3. `meeting` の判定が「重複：打合せ（…）」で表示され、文字色が会食と同じ
4. 既存の受入条件（Phase 3-A §4）が引き続き通る

## コミット案
`learning-radar: 判定の照合をeventId→URL＋開催日→タイトル＋開催日の順に（取込の重複判定と同じ正規化）。verdictに meeting（重複：打合せ）を追加、未知のverdictはlabelをそのまま表示`
