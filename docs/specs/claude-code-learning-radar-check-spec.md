# 依頼書：学びレーダー Phase 3-A — カレンダー判定（learning-check.json）の取込と表示

作成：2026-10-03 設計チャット／対象：`learning-radar/index.html`（＋`sw.js` の版上げ）
土台：main 最新。作業前に `git pull` し、HEAD を報告に記載。
対になる文書：Cowork恒久ルールパッチ「学びチェック」（同日発行）。判定ファイルの定義は両文書で同一。**こちらの §2 が正本**。

## 1. 目的
Coworkのチェッカーがカレンダーと突き合わせた結果（判定）を、学びレーダーのカードに1行で表示する。本人がカレンダーを開いて一つずつ確かめなくてよい状態にする。

## 2. 判定ファイル `learning-check.json`（正本定義）
置き場：Drive `10_日次データ`（`GDRIVE_FOLDER_ID` と同じフォルダ）。Coworkが**同名で新規作成**する（学びレーダー収集と同じ流儀）。OSは `createdTime` 最新の1件を採用する。

```json
{
  "generatedAt": "2026-10-06T08:40:00+09:00",
  "source": "cowork-learning-check",
  "rangeTo": "2026-11-06",
  "checks": [
    { "eventId": "lr_0042", "verdict": "ok",       "label": "重複なし",
      "detail": "10/16（木）13:00〜17:00 は空き。前後の移動も問題なし", "conflicts": [], "proposal": null },
    { "eventId": "lr_0057", "verdict": "routine",  "label": "重複：ルーチン（◎1dayチェック）→ 移動可",
      "detail": "10/23（木）10:00〜10:30 に ◎1dayチェック",
      "conflicts": [{ "kind": "routine", "title": "◎1dayチェック", "when": "2026-10-23T10:00" }],
      "proposal": { "type": "moveRoutine", "title": "◎1dayチェック", "to": "2026-10-24T13:00" } },
    { "eventId": "lr_0061", "verdict": "dinner",   "label": "重複：会食（確定）",
      "detail": "10/30（木）19:00〜 会食：〇〇社", "conflicts": [{ "kind": "dinner", "title": "会食：〇〇社", "when": "2026-10-30T19:00" }], "proposal": null },
    { "eventId": "lr_0063", "verdict": "away",     "label": "重複：出張・合宿",
      "detail": "11/4（火）は ◎大阪", "conflicts": [{ "kind": "away", "title": "◎大阪", "when": "2026-11-04" }], "proposal": null },
    { "eventId": "lr_0064", "verdict": "dinnerRule","label": "家ごはん枠に当たる",
      "detail": "11/5（水）19:00〜21:00。その週は夜不在がすでに3日", "conflicts": [], "proposal": null },
    { "eventId": "lr_0065", "verdict": "unknown",  "label": "時間 要確認",
      "detail": "開催時間が未記載。終日なら 11/7（金）は空き", "conflicts": [], "proposal": null }
  ]
}
```

- `verdict` は6値固定：`ok / routine / dinner / away / dinnerRule / unknown`
- `label` は画面にそのまま出す（OS側で言い換えない）。`verdict` ごとの既定文言は上のとおり。`routine` だけ括弧内にルーチン名が入る
- `detail` は展開時のみ表示。`proposal` があれば展開時に「移動案：◎1dayチェック → 10/24（金）13:00」の形で表示
- `eventId` は学びレーダーの `events[].id`。該当が無い判定は捨てる
- `generatedAt` が `settings.lastCheckGeneratedAt` と同じなら再取込しない

## 3. 仕様

### 3-1. 取込（既存の「⬇ 取込」に相乗り。新しいボタン・画面は増やさない）
- `startImport()` で `learning-events.json` の取込（成功・失敗を問わず）のあとに、同じトークンで `learning-check.json` を探して読む。無ければ何もしない（エラー表示も出さない）
- 実装は `gdriveFindFile` / `gdriveLoad` を**ファイル名を引数に取れる形に一般化**して使い回す（`GDRIVE_FILE_NAME` の直書き箇所を増やさない）。Drive未認可のときはファイル選択／貼り付け欄で `learning-check.json` も受け付ける（`checks` 配列を持つJSONなら判定として扱う。`newEvents` なら従来どおり）
- 保存：`S.settings.checks = { [eventId]: { verdict, label, detail, conflicts, proposal, checkedAt: generatedAt } }`。`settings.lastCheckGeneratedAt` を更新。`saveData()` 経由で `learningRadar_v1` に入る（Task OS バックアップには自動で含まれる）
- `normalizeData()` で `settings.checks` が無い旧データは `{}` に補う
- 取込結果の文言に判定の件数は出さない（静かなUI）。「判定を取り込みました（10/6 08:40 時点）」の1行だけ

### 3-2. 表示（カードの右列、締切表示の直下に1行）
- 対象の節：見過ごしを除く全節（締切接近・新着・検討中・申込済み）。過去・見送りの折りたたみ内では出さない
- 判定が無いカードには何も出さない（「未判定」も出さない）
- 色：`ok` はレーダー色（`--radar`）。`dinner / away / dinnerRule` は文字色を `--tx`（濃い字）。`routine / unknown` は `--tx2`。**赤は使わない**（赤は締切専用）
- 展開時：`detail` を「判定」の行として、`proposal` があれば「移動案」の行として `kv` 形式で表示。既存のインライン編集欄の上に置く
- 判定の `checkedAt` が開催日の変更より古い場合（`e.updatedAt` があればそれと比較。無ければ比較しない）、ラベル末尾に「（日程変更前の判定）」を添える
- 判定は参考情報。ステータスは変えない。申込・見送り後も `checks` は消さない

### 3-3. 既存の決定に合わせること
- 件数バッジ・催促・「0件」表示を入れない／モーダルを作らない／節の順序と折りたたみは現状どおり
- 定期実行は作らない。取込は本人操作のみ

## 4. 受入条件
1. `learning-check.json` を Drive に置いて「⬇ 取込」→ 該当カードに `label` が1行で出る。無い予定は無変更
2. 同じ `generatedAt` のファイルを再取込しても変化なし。新しい `generatedAt` なら上書き
3. `eventId` が存在しない判定は無視され、エラーにならない
4. 展開で `detail`・`proposal` が読める。`proposal` が null の判定では「移動案」行が出ない
5. Drive未認可のとき、貼り付け欄に `checks` を持つJSONを貼ると同じ結果になる
6. 判定を持つ予定を申込・見送りにしても `checks` は残り、バックアップ（`learningRadar_v1`）に含まれる
7. 既存の取込（`newEvents`）・インライン編集・設定画面・レーダー帯が従来どおり動く（回帰なし）
8. 375px で横スクロールが出ない。赤色が締切以外に使われていない

## 5. テスト用サンプル
seed 67件を取り込んだ状態で、§2 のJSON（`eventId` は seed の先頭6件の id に置き換え）を貼り付けて取り込む。期待：6枚のカードに6種類の `label` が出て、展開で `detail` が読め、`lr_0057` 相当にだけ「移動案」が出る。

## 6. 変更しないこと
- `importPayload`（新着の取込）・重複判定・除外語・`dismissed`・Drive認可の流れ・Task OS 側

## コミット案
`learning-radar: カレンダー判定（learning-check.json）を取込時に読み、カードに判定1行（重複なし／ルーチン→移動可／会食／出張・合宿／家ごはん枠／時間要確認）を表示。展開で詳細と移動案。settings.checks に保存しバックアップへ`
