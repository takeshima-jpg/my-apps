# シート台帳（Project OS ⇔ スプレッドシート）

Claude Codeが「◯◯のシートを更新して」の依頼を解釈するための対応表。

> **このリポジトリは公開（PUBLIC）です。** プロジェクト名や spreadsheetId は個人情報のため、
> **実データはこの `sheets.md` には書かず、`docs/sheets.local.md`（.gitignoreで追跡除外）に記入**する。
> `sheets.local.md` は同じ表形式で、初回に所有者へURLを確認して Claude Code が記入する。
> （リポジトリを private にする場合は、この方針を見直して本ファイルに直接記入してよい）

## 記入フォーマット（`docs/sheets.local.md` 側に書く）

```
| プロジェクト名 | spreadsheetId | gid | 備考 |
|----------------|---------------|-----|------|
| （PJ名）       | （URLのd/〜/の部分） | （URLの gid=） | 11列・ID=テーマ番号×10+連番 |
```

spreadsheetId と gid は、Project OS のプロジェクト編集に登録されている
スプレッドシートURL `https://docs.google.com/spreadsheets/d/<spreadsheetId>/edit?gid=<gid>` から取れる。

## シートの列構成（11列 / A:K）

`ID / テーマ / 種別 / 期日 / 状態 / イベント / 担当 / 対象 / 施策 / ゴール（狙い） / 結果`

- **種別**：空欄=イベント ／ `分岐` ／ `制約` ／ `記録`
- **ID の採番規則**：テーマ番号 × 10 ＋ 連番（例：テーマ2 → 21, 22, 23…）。
  新規行はこの規則で次番を振る。規則が読み取れなければ所有者に1問確認する。
- **日付形式**：シートの既存表記（`YYYY/MM/DD` など）に合わせる。

## 更新の手順

`docs/specs/claude-code-sheets-integration-spec.md` に従う。要点：

1. `tools/sheet_update.py <spreadsheetId> --get` で現状取得
2. 変更差分（何行のどの列がどう変わるか）をチャットに提示 → 所有者の「OK」を待つ
3. 承認後に書き込み（`--set-status` / `--append-tsv`。ツールが書き込み前に自動でバックアップを取る）
4. `--get` で反映を確認し、「Project OSで『⟳ シートから直接取り込み』を押してください」と報告
5. 行削除はしない（状態変更・行追加のみ。削除は所有者がシートで直接行う）
