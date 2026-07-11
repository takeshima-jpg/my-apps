> ✅ 実装済み 2026-07-10 ・ コミット 4cfc2f6

# Claude Code 実装依頼書：tools/weekly_facts.py（週次「事実の差分」）＋Cowork追補

## 目的
週次レビューの「成果／停滞」の数字を、AIの解釈ではなく**機械計算の事実**にする。
Claude Codeが差分JSONを作り、Coworkはその数字をそのまま使う。

## 実装：tools/weekly_facts.py

### 使い方
```
python tools/weekly_facts.py <今週のbackup.json> <先週のスナップショット.json>
```
出力：`aix_weekly_facts.json`（Coworkの作業フォルダに置く用）＋ 標準出力にmarkdown表

### 計算する事実（すべてデータから機械計算。推測禁止）
```json
{
  "period": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},
  "shot": {"completed": N, "created": N, "overdue_now": N, "overdue_prev": N},
  "lectica": {"logged_days": N, "logs": N, "completed_experiments": N, "active_now": N},
  "oneday": {"logged_days": N, "missing_days": ["YYYY-MM-DD", ...]},
  "top10_contact": {"contacted": N, "total": N, "not_contacted_names": [...]},
  "next_experience": {"set": N, "executed_this_week": N},
  "projects": {"important_no_activity": [{"name": "...", "days_stale": N}, ...]},
  "hitomemo": {"changelog_entries_this_week": N}
}
```
- 「今週」= 先週スナップショットのsavedAt 〜 今週backupのsavedAt
- shot.completed：completedAt がこの期間内のもの
- lectica.logged_days：lecticaLogs の date のユニーク日数（期間内）
- top10_contact：socialUniverse isTop10=true の人物のうち、hitomemo lastContactDate が期間内の人数と未接触者名
- next_experience.executed：nextExperience設定者のうち changeLog に期間内の「経験」系ログがある人数
- projects.important_no_activity：重要度A/高 かつ 期間内に対応Shot完了・イベント更新が無いPJ
- 既存の check_backup_health.py と関数を共有できる部分は共通化してよい

### 検証
架空の2スナップショットでユニットテスト（完了数・接触数・欠落日の計算が正しいこと）を書いて実行。

## Cowork側の追補（週次レビュー仕様v2への追記）

STEP4B（週次生成）の冒頭に追加：
```
作業フォルダに aix_weekly_facts.json があれば読み込み、「今週の成果／停滞」「育成レビュー」
「経営パートナー進捗」の数字はこのファイルの値をそのまま使う（自分で数え直さない・改変しない）。
ファイルが無い週は従来どおりバックアップから読むが、数字には「（概算）」を付ける。
```

## 運用フロー
1. 週次レビューの朝、Claude Codeで「今週の事実差分を出して」（backupと先週スナップショットを指定）
2. 生成された aix_weekly_facts.json をCoworkの作業フォルダにコピー
3. Coworkが週次レビューを生成（数字は事実ファイル準拠）
※ 慣れたら1をタスクスケジューラで自動化可能（日曜朝）
