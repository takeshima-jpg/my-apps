# docs 一覧

my-apps（竹嶋OS）の設計・手順・プロンプトの置き場。

- **specs/** … 実装依頼書・手順書（設計はここを参照）
- **prompts/** … 壁打ち・Coworkプロンプト類（プロンプトはここを参照）
- **archive/** … 上位版に統合された・内容が古くなったファイル（削除ではなくここへ退避）。現時点で該当なし
- 直下の `sheets.md` / `sheets.local.md` は台帳（specs/promptsではない運用データ）

状態の凡例：✅実装済み（コミット済み）／🕒未実装（依頼書のみ）／🔧運用中（手順書・繰り返し使う）

## specs/ — 実装依頼書・手順書

| ファイル | 用途 | 状態 |
|---|---|---|
| [claude-code-cockpit-shell-spec.md](specs/claude-code-cockpit-shell-spec.md) | launcherを統合コックピット（左タブ＋iframe保持＋「今日」タブ）に昇格 | ✅実装済み 2026-07-12 `cf7927c` |
| [claude-code-cockpit-improve-v1-spec.md](specs/claude-code-cockpit-improve-v1-spec.md) | コックピット改善v1（OSアイコン統一・右余白解消・追加バーsticky・ログイン導線・AIタスク読込導線） | ✅実装済み 2026-07-12 `737f06b` |
| [claude-code-100list-import-spec.md](specs/claude-code-100list-import-spec.md) | 100listにAI取り込みページ（【やりたいこと】ブロック貼り付けで登録） | ✅実装済み 2026-07-12 `5ddc74f` |
| [claude-code-sparring-buttons-spec.md](specs/claude-code-sparring-buttons-spec.md) | reflect-osに壁打ちプロンプトのコピーボタンを追加 | ✅実装済み 2026-07-11 `b6e6574` |
| [claude-code-weekly-facts-spec.md](specs/claude-code-weekly-facts-spec.md) | tools/weekly_facts.py（週次「事実の差分」）＋Cowork追補 | ✅実装済み 2026-07-10 `4cfc2f6` |
| [claude-code-cockpit-autoimport-spec.md](specs/claude-code-cockpit-autoimport-spec.md) | コックピット起動時にAIタスクを1日1回自動取り込み（非表示iframe＋postMessage） | 🕒未実装 |
| [claude-code-launcher-pwa-spec.md](specs/claude-code-launcher-pwa-spec.md) | コックピットのPWA化＋自作SVGアイコン（ホーム追加・standalone表示） | ✅実装済み 2026-07-12 `89f825e` |
| [claude-code-launcher-display-tweak-spec.md](specs/claude-code-launcher-display-tweak-spec.md) | ランチャーOS表示調整（名称統一・アイコンをTask OSと差別化・文字サイズ拡大） | ✅実装済み 2026-07-12 `9d14778` |
| [claude-code-minutes-triage-spec.md](specs/claude-code-minutes-triage-spec.md) | 議事録→OS振り分け（inbox triage）の手順書。「inboxを振り分けて」で発動 | 🔧運用中（手順書） |
| [claude-code-sheets-integration-spec.md](specs/claude-code-sheets-integration-spec.md) | スプレッドシート連携（Project OS直接取り込み＋シート更新ツール）の設計・手順 | 🔧運用中（手順書） |

## prompts/ — 壁打ち・Coworkプロンプト

| ファイル | 用途 | 状態 |
|---|---|---|
| [reflect-sparring-prompt.md](prompts/reflect-sparring-prompt.md) | Reflect壁打ち（内省→記録→行動）。reflect-osのコピーボタンから起動 | 🔧運用中 |
| [lectica-sparring-prompt.md](prompts/lectica-sparring-prompt.md) | Lectica実験の壁打ち（具体化→実行→Reflect記録） | 🔧運用中 |

※ koso壁打ち・morning-brief系のプロンプトは各OS本体（koso-logのAI取り込み等）やCowork側に埋め込まれており、独立ファイルは現状これら2件のみ。

## 台帳（specs/promptsではない運用データ）

| ファイル | 用途 | 状態 |
|---|---|---|
| [sheets.md](sheets.md) | Project OS ⇔ スプレッドシートの対応表（公開可の枠組みのみ） | 🔧運用中 |
| sheets.local.md | シートの実データ（プロジェクト名・spreadsheetId。個人情報のためgitignore） | 🔧ローカルのみ |
