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
| [claude-code-cockpit-brief-colors-spec.md](specs/claude-code-cockpit-brief-colors-spec.md) | 今日タブのBrief見出しをbrief-viewerと同じカテゴリ色分けに | ✅実装済み 2026-07-12 `90d5303` |
| [claude-code-hitomemo-stage-spec-v2.md](specs/claude-code-hitomemo-stage-spec-v2.md) | ヒトメモ関係ステージ4段階＋🤝稼働フラグ改修（承認付き移行・SU/health追従）。正本=[partner-stage-legend-v1-1](partner-stage-legend-v1-1.md) | ✅実装済み 2026-07-12 `05cffb7`/`1b78a64` |
| [claude-code-hitomemo-form-ui-spec-v2.md](specs/claude-code-hitomemo-form-ui-spec-v2.md) | ヒトメモ編集フォームUI改善（長文欄拡大・pillボタン化・関わり方タイプに「家族」追加・旧値保持） | ✅実装済み 2026-07-12 `fd5c7d0` |
| [claude-code-1day-slim-spec.md](specs/claude-code-1day-slim-spec.md) | 1dayのタグ8種・ブログ/VISION/エネ高フラグを撤去、満足度を◎〇△×の4段階に（違和感/深掘りは存続） | ✅実装済み 2026-07-12 `062b887` |
| [claude-code-taskos-aiimport-hotfix-spec.md](specs/claude-code-taskos-aiimport-hotfix-spec.md) | Task OS AIタスク読込の緊急修正（genId未定義→共通genUidに統一・GDrive dedupe隔離確認） | ✅実装済み 2026-07-12 `bfec392` |
| [claude-code-taskos-collect-parse-hotfix.md](specs/claude-code-taskos-collect-parse-hotfix.md) | Task OS 同期の緊急修正（collectAllOSDataが週次/月次briefのmarkdownをJSON.parseして落ちる→安全パース＋restore対称化） | ✅実装済み 2026-07-12 `8bf0153` |
| [claude-code-taskos-dedupe-403-quiet-spec.md](specs/claude-code-taskos-dedupe-403-quiet-spec.md) | GDrive dedupeの403（所有外trash不可）を静音スキップ・セッション再試行なし・ログ洪水解消 | ✅実装済み 2026-07-12 `ad3bad8` |
| [claude-code-drive-cleanup-unify-spec.md](specs/claude-code-drive-cleanup-unify-spec.md) | Drive掃除を一本化（ブラウザ側dedupe廃止＋drive_cleanup.py週1手動）。手順=[drive-cleanup-運用](specs/drive-cleanup-運用.md) | ✅実装済み 2026-07-12 `a541b5b` |
| [drive-cleanup-運用.md](specs/drive-cleanup-運用.md) | drive_cleanup.py の週1手動運用手順書（dry-run→本番・掃除ルール） | 🔧運用中（手順書） |
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
