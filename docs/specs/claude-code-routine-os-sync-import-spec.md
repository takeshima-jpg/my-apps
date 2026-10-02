# 依頼書：Routine OS「同期取込（ROUTINE-IMPORT）」機能

作成日：2026-10-02　作成：Cowork（routine-calendar-sync スキル）　対象：Routine OS v2（single-file HTML）

## 目的

Cowork の「ルーチンチェック」（routine-calendar-sync スキル）が、カレンダーとルーチンOSの差分を検出したときに、**ルーチンOS側の修正も Cowork から渡せる**ようにする。
現状 Cowork はバックアップ JSON を読むだけで、ルーチンOSへの書き込み手段がない。既存の Task OS「AIタスク読込（daily-tasks.json）」、Reflect OS「REFLECT-IMPORT」と同じ思想で、**ルーチンOSが取込口を持つ**形にする。

設計憲章に合わせ、ゼロ依存・ローカルファースト・OSが正（Cowork は提案を渡すだけ、適用はOS側で人が押す）。

## フェーズ構成

- **Phase 1（今回）**：テキスト貼り付け取込。Cowork が `【ROUTINE-IMPORT】…【/ROUTINE-IMPORT】` ブロックを出力 → 竹嶋さんがルーチンOSの取込画面に貼る → プレビュー → 適用。
- **Phase 2（後日・任意）**：Drive の `10_日次データ/routine-sync.json` を起動時に自動で読んで同じ処理にかける（cockpit-autoimport と同じ非表示 iframe / postMessage 方式、または GDrive 読み取り）。Phase 1 のパーサ・適用ロジックをそのまま使う。

## 取込フォーマット（Phase 1 / Phase 2 共通）

```
【ROUTINE-IMPORT】
{
  "version": 1,
  "source": "cowork/routine-calendar-sync",
  "issuedAt": "2026-10-02T09:00:00+09:00",
  "ops": [
    { "opId": "2026-10-02-001", "op": "add",
      "task": { "title": "SU印刷", "cycle": "不定期", "dept": "個人", "layer": 3,
                "deliverable": "作成したSUを出社日に印刷する", "note": "カレンダー名：◎SU印刷" } },
    { "opId": "2026-10-02-002", "op": "add",
      "task": { "title": "PJ見直し", "cycle": "隔週", "dept": "個人", "layer": 3,
                "nextDate": "2026-10-15", "note": "カレンダー名：◎V：PJ打合せ（隔週木16:00）" } },
    { "opId": "2026-10-02-003", "op": "update", "id": 64,
      "patch": { "cycle": "四半期", "note": "カレンダー名：◎V：ソーシャルユニバース（3か月に1回120分）" } },
    { "opId": "2026-10-02-004", "op": "update", "id": 19,
      "patch": { "title": "PL、BS実績記入", "note": "BS記入(14)を統合。カレンダー名：◎PL、BS実績記入" } },
    { "opId": "2026-10-02-005", "op": "update", "id": 14,
      "patch": { "title": "bixidチェック", "cycle": "月次", "note": "PL、BS実績記入の2週間後。CF記入を兼ねる" } },
    { "opId": "2026-10-02-006", "op": "stop", "id": 38 }
  ]
}
【/ROUTINE-IMPORT】
```

- `op` は `add` / `update` / `stop`（status を「停止」に）/ `resume`（「未完了」に戻す）の4種。**`delete` は作らない**（アーカイブ思想・消さない）。
- `add` の `task` は既存タスクと同じ項目名（title, cycle, dept, layer, nextDate, deliverable, notifyMsg, url, note, addType, addBase, addDays, excludeWeekends, excludeHolidays, skippable）。未指定は既存の新規作成と同じ既定値。`id` はOS側が採番。
- `update` / `stop` / `resume` は `id` で特定。`patch` にある項目だけ上書き。`id` が存在しなければその op はエラー表示してスキップ（他の op は続行）。
- `opId` で冪等化：適用済み opId を `routineOS.appliedOps`（配列、上限500・古いものから落とす）に保存し、同じ opId は「適用済み」として無視。同じブロックを2回貼っても二重登録しない。
- `nextDate` を渡さない `add` は、cycle から既存ロジックで算出（既存の「新規追加」と同じ）。

## UI

- 左メニュー（または設定）に「⬇ 同期取込」を1つ追加。モーダルは作らず、既存の追加フォームと同じ1画面構成で：
  1. テキストエリア（ブロックを貼る）
  2. 「プレビュー」→ 下に **差分表**（op／対象／変更前→変更後／状態＝新規・変更・停止・適用済み・エラー）
  3. 「適用」ボタン（エラー0件でなくても、エラー行以外を適用できる）
  4. 適用後、結果を1行サマリー（例「追加2・変更3・停止1・スキップ0」）と `routineOS.logs` に `action:"同期取込"` で1件記録（memo に opId 一覧）
- 貼られたテキストから `【ROUTINE-IMPORT】…【/ROUTINE-IMPORT】` の中身だけを抜く（前後に会話文が混ざっていても動く）。JSON パース失敗時は行番号付きでエラー表示。
- 催促・バッジ・通知は付けない（静かなUI）。

## データ・バックアップ

- 変更はすべて既存の `saveData()` 系を通す（GDrive バックアップ・restore guard に乗る）。
- `routineOS.appliedOps` を `collectAllOSData()` の収集対象に含める（Task OS 側の対応が必要なら別小依頼）。
- 旧形式データの移行なし（既存タスクの構造は変えない）。

## 受入条件

1. 上記サンプルブロックを貼ってプレビューすると、6 op の差分表が出る（id 38 は「停止」、存在しない id を混ぜたらその行だけエラー）。
2. 適用後、タスク一覧に「SU印刷」「PJ見直し」が増え、id 64 の cycle が四半期、id 19 の title が「PL、BS実績記入」になっている。
3. 同じブロックをもう一度貼って適用 → 全行「適用済み」で何も変わらない。
4. 会話文を含むテキストを貼っても、ブロック部分だけが処理される。
5. 既存のタスク追加・完了・スキップ・バックアップが従来どおり動く。
6. 1ファイル完結・外部依存なし。

## Cowork 側（参考・このスキルで対応）

- routine-calendar-sync スキルの出力末尾「ルーチンOSで直すこと」を、この `【ROUTINE-IMPORT】` ブロックとして出す。竹嶋さんが「適用した」と言ったら対応表を更新。
- Phase 2 に進むときは、同じ JSON を Drive `10_日次データ/routine-sync.json` に書き出す（createdTime 最新を正、他の日次ファイルと同じ運用）。
