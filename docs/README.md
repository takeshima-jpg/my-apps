# docs 一覧

my-apps（竹嶋OS）の設計・手順・プロンプトの置き場。

- **specs/** … 実装依頼書・手順書（設計はここを参照）
- **prompts/** … 壁打ち・Coworkプロンプト類（プロンプトはここを参照）
- **archive/** … 上位版に統合された・内容が古くなったファイル（削除ではなくここへ退避）
  - [claude-code-hitomemo-manual-sort-spec.md](archive/claude-code-hitomemo-manual-sort-spec.md) … sort-collapse-specと同一内容の重複（実装済み `fd0ebe9`。正本はspecs側）
  - [reflect-sparring-instructions-v2.md](archive/reflect-sparring-instructions-v2.md) … Reflect壁打ちv2の持ち込み原稿（prompts/reflect-sparring-prompt.md へ反映済み。正本はprompts側）
- 直下の `sheets.md` / `sheets.local.md` は台帳（specs/promptsではない運用データ）

状態の凡例：✅実装済み（コミット済み）／🕒未実装（依頼書のみ）／🔧運用中（手順書・繰り返し使う）

## specs/ — 実装依頼書・手順書

| ファイル | 用途 | 状態 |
|---|---|---|
| [claude-code-cockpit-shell-spec.md](specs/claude-code-cockpit-shell-spec.md) | launcherを統合コックピット（左タブ＋iframe保持＋「今日」タブ）に昇格 | ✅実装済み 2026-07-12 `cf7927c` |
| [claude-code-cockpit-improve-v1-spec.md](specs/claude-code-cockpit-improve-v1-spec.md) | コックピット改善v1（OSアイコン統一・右余白解消・追加バーsticky・ログイン導線・AIタスク読込導線） | ✅実装済み 2026-07-12 `737f06b` |
| [claude-code-100list-import-spec.md](specs/claude-code-100list-import-spec.md) | 100listにAI取り込みページ（【やりたいこと】ブロック貼り付けで登録） | ✅実装済み 2026-07-12 `5ddc74f` |
| [claude-code-sparring-buttons-spec.md](specs/claude-code-sparring-buttons-spec.md) | reflect-osに壁打ちプロンプトのコピーボタンを追加 | ✅実装済み 2026-07-11 `b6e6574` |
| [claude-code-weekly-facts-spec.md](specs/claude-code-weekly-facts-spec.md) | tools/weekly_facts.py（週次「事実の差分」）＋Cowork追補 | ✅実装済み 2026-07-10 `4cfc2f6`／2026-07-17 に単一バックアップ＋週窓方式の新版へ差し替え（旧版は tools/archive/、運用は tools/README.md §2） |
| [claude-code-cockpit-autoimport-spec.md](specs/claude-code-cockpit-autoimport-spec.md) | コックピット起動時にAIタスクを1日1回自動取り込み（非表示iframe＋postMessage） | 🕒未実装 |
| [claude-code-launcher-pwa-spec.md](specs/claude-code-launcher-pwa-spec.md) | コックピットのPWA化＋自作SVGアイコン（ホーム追加・standalone表示） | ✅実装済み 2026-07-12 `89f825e` |
| [claude-code-launcher-display-tweak-spec.md](specs/claude-code-launcher-display-tweak-spec.md) | ランチャーOS表示調整（名称統一・アイコンをTask OSと差別化・文字サイズ拡大） | ✅実装済み 2026-07-12 `9d14778` |
| [claude-code-cockpit-brief-colors-spec.md](specs/claude-code-cockpit-brief-colors-spec.md) | 今日タブのBrief見出しをbrief-viewerと同じカテゴリ色分けに | ✅実装済み 2026-07-12 `90d5303` |
| [claude-code-hitomemo-stage-spec-v2.md](specs/claude-code-hitomemo-stage-spec-v2.md) | ヒトメモ関係ステージ4段階＋🤝稼働フラグ改修（承認付き移行・SU/health追従）。正本=[partner-stage-legend-v1-1](partner-stage-legend-v1-1.md) | ✅実装済み 2026-07-12 `05cffb7`/`1b78a64` |
| [claude-code-hitomemo-form-ui-spec-v2.md](specs/claude-code-hitomemo-form-ui-spec-v2.md) | ヒトメモ編集フォームUI改善（長文欄拡大・pillボタン化・関わり方タイプに「家族」追加・旧値保持） | ✅実装済み 2026-07-12 `fd5c7d0`（家族選択肢は後続で撤回） |
| [claude-code-hitomemo-family-sort-spec.md](specs/claude-code-hitomemo-family-sort-spec.md) | 家族を独立カテゴリ(personType=family)に分離しパートナー形成ロジックから除外＋一覧の並び替え/区分フィルタ | ✅実装済み 2026-07-13 `4276cef` |
| [claude-code-1day-slim-spec.md](specs/claude-code-1day-slim-spec.md) | 1dayのタグ8種・ブログ/VISION/エネ高フラグを撤去、満足度を◎〇△×の4段階に（違和感/深掘りは存続） | ✅実装済み 2026-07-12 `062b887` |
| [claude-code-taskos-home-cleanup-spec.md](specs/claude-code-taskos-home-cleanup-spec.md) | Task OS HOMEの重複3セクション（今日のLectica・100リスト・PROJECT）を撤去（ランチャー今日タブへ移行） | ✅実装済み 2026-07-13 `b8df725` |
| [claude-code-launcher-lectica-spec.md](specs/claude-code-launcher-lectica-spec.md) | ランチャー今日タブのLectica全文表示＋Shot追加・壁打ちコピー・Reflect記録の動線 | ✅実装済み 2026-07-13 `3217981` |
| [hitomemo-contact-autoupdate-spec.md](specs/hitomemo-contact-autoupdate-spec.md) | ヒトメモ接点の自動更新（aix-hitomemo.json contacts配列→最終接触日/接点ログ。鮮度ガード・冪等・14日窓） | ✅Part B実装済み 2026-07-16 `dccd83c`／🕒Part A Cowork適用待ち |
| [claude-code-hitomemo-sort-collapse-spec.md](specs/claude-code-hitomemo-sort-collapse-spec.md) | ヒトメモ一覧のステージ別グルーピング折りたたみ（記録のみ・家族は既定閉・開閉状態保存・未分類グループ・並べ替えはグループ内適用） | ✅実装済み 2026-07-16 `fd0ebe9` |
| [claude-code-project-os-v2-spec.md](specs/claude-code-project-os-v2-spec.md) | Project OS v2.1「考える場所」への転換（核3行・PJカードホーム・詳細1画面化・クイック追加・壁打ち出力・PROJECT-IMPORT・共有用エクスポート・アラート転換） | ✅実装済み 2026-07-18 `f1e9085`/`f40e4c5`/`c15e43a` |
| [claude-code-task-os-home-v2-spec.md](specs/claude-code-task-os-home-v2-spec.md) | Task OS HOME見直し（統計3カード撤去・今日の一手をpos_v4の次の一手に刷新・今日やること既定展開・日付表示修正） | ✅実装済み 2026-07-18 `a2b6c84` |
| [claude-code-reflect-tankyu-board-spec.md](specs/claude-code-reflect-tankyu-board-spec.md) | Reflect OS 探求ボード（問い/実験/原則の独立データ化・冪等移行・統合/整理モード・振り返り・実践原則・ホーム刷新・新規動線接続） | ✅実装済み 2026-07-19 `6b62cdd`/`c194db4`/`9743082` |
| [claude-code-task-os-home-viewpoints-spec.md](specs/claude-code-task-os-home-viewpoints-spec.md) | Task OS HOME視点追加（🧭PJの現在地ミニ＋💡最近の気づき1件。読み取り専用・該当なし非表示・催促なし） | ✅実装済み 2026-07-19 `53b9585` |
| [claude-code-project-os-v2-2-spec.md](specs/claude-code-project-os-v2-2-spec.md) | Project OS v2.2（中央寄せmax-width 920px・文字拡大・見立て4項目＝成功条件/悪い未来/センターピン/注意点のインライン編集・壁打ち出力へ反映） | ✅実装済み 2026-07-19 `b4404b1` |
| [claude-code-reflect-board-quick-add-spec.md](specs/claude-code-reflect-board-quick-add-spec.md) | 探求ボードのフリー追加（＋問い/＋実験＝candidate作成・問い未設定可）＋取り込み画面に習慣/思考法の混在防止ルール表示 | ✅実装済み 2026-07-19 `3d4495a` |
| [claude-code-reflect-project-sync-spec.md](specs/claude-code-reflect-project-sync-spec.md) | Reflect のProject同期をv2.2追従（centerPin/badFuture/successConditions等をテーマへ空欄補完・手入力は上書きしない・PJ削除時は手動テーマ化） | ✅実装済み 2026-07-19 `99dfb66` |
| [claude-code-reflect-decision-review-spec.md](specs/claude-code-reflect-decision-review-spec.md) | 実験に決定検証種別（expType='review'）を追加。PJ外の意思決定検証を🔍で区別し検証日=deadlineで既存の振り返り→原則化フローに接続 | ✅実装済み 2026-07-19 `bcf2ab1` |
| [claude-code-reflect-import-cleanup-spec.md](specs/claude-code-reflect-import-cleanup-spec.md) | 取り込み画面の壁打ちプロンプトコピーボタン4種を撤去（壁打ちはclaude.aiプロジェクトで運用）。定数は残置 | ✅実装済み 2026-07-19 `7239441` |
| [claude-code-reflect-decision-menu-spec.md](specs/claude-code-reflect-decision-menu-spec.md) | 意思決定検証を左メニューに独立（探求ボードから分離・要検証/検証待ち/検証済みの区分・3枠別管理・【意思決定ログ】取り込み） | ✅実装済み 2026-07-19 `2da4c91` |
| [claude-code-project-os-bulk-edit-spec.md](specs/claude-code-project-os-bulk-edit-spec.md) | 旧イベント・旧分岐一覧の複数選択→一括削除/完了（確認1回・すべて選択・forks削除時はmoves同ID連動削除） | ✅実装済み 2026-07-19 `730498b` |
| [claude-code-task-os-lectica-shot-replace-spec.md](specs/claude-code-task-os-lectica-shot-replace-spec.md) | autoGenLecticaShot：ランダム生成由来かつ未完了の当日Lectica Shotを後着の参謀提案で差し替え（lecticaSource由来フラグ・冪等） | ✅実装済み 2026-07-20 `857c826` |
| [claude-code-taskos-mobile-menu-fix-spec.md](specs/claude-code-taskos-mobile-menu-fix-spec.md) | Task OSスマホのハンバーガーメニューが開かない緊急修正（toggleSidebar/closeSidebar未定義を実装） | ✅実装済み 2026-07-13 `ed3f6b6` |
| [claude-code-taskos-aiimport-hotfix-spec.md](specs/claude-code-taskos-aiimport-hotfix-spec.md) | Task OS AIタスク読込の緊急修正（genId未定義→共通genUidに統一・GDrive dedupe隔離確認） | ✅実装済み 2026-07-12 `bfec392` |
| [claude-code-taskos-collect-parse-hotfix.md](specs/claude-code-taskos-collect-parse-hotfix.md) | Task OS 同期の緊急修正（collectAllOSDataが週次/月次briefのmarkdownをJSON.parseして落ちる→安全パース＋restore対称化） | ✅実装済み 2026-07-12 `8bf0153` |
| [claude-code-taskos-dedupe-403-quiet-spec.md](specs/claude-code-taskos-dedupe-403-quiet-spec.md) | GDrive dedupeの403（所有外trash不可）を静音スキップ・セッション再試行なし・ログ洪水解消 | ✅実装済み 2026-07-12 `ad3bad8` |
| [claude-code-drive-cleanup-unify-spec.md](specs/claude-code-drive-cleanup-unify-spec.md) | Drive掃除を一本化（ブラウザ側dedupe廃止＋drive_cleanup.py週1手動）。手順=[drive-cleanup-運用](specs/drive-cleanup-運用.md) | ✅実装済み 2026-07-12 `a541b5b` |
| [claude-code-lectica-single-source-spec.md](specs/claude-code-lectica-single-source-spec.md) | 【v2】Lectica出題をCowork提案優先に（ランダムはallowRandom引数で同期・AIタスク読込時のみに降格・未ログイン起動時は非生成。追補：launcher addLecticaShotの二重防止をカテゴリ基準に統一） | ✅実装済み 2026-08-18 |
| [claude-code-lectica-skip-autopause-spec.md](specs/claude-code-lectica-skip-autopause-spec.md) | Lectica日次スキップを自動pause化（期日超過の未完了LecticaShotをlecticaAutoPausedとしてpendingへ・手動スキップボタンと保留ログ記録を廃止・recent判定維持） | ✅実装済み 2026-08-18 |
| [claude-code-brief-evidence-collapse-spec.md](specs/claude-code-brief-evidence-collapse-spec.md) | Brief本文の根拠ブロック（─根拠─〜）をdetailsで既定折りたたみ（brief-viewer/1day両方のmarkdownToHtmlを同期・マーカー無しは従来どおり） | ✅実装済み 2026-08-18 |
| [claude-code-reflect-nav-consolidation-spec.md](specs/claude-code-reflect-nav-consolidation-spec.md) | 【A】Reflect OS 導線整理（ホーム重点を閲覧専用化・テーマ未紐づけをログ内フィルタへ・検索をアーカイブに統合＝ナビ10→8）＋重点スナップショット reflect_focus_v1 をlocalStorageへミラー（Bの前提） | ✅実装済み 2026-08-18 |
| [claude-code-taskos-focus-display-spec.md](specs/claude-code-taskos-focus-display-spec.md) | 【B・要A先行】Task OS HOMEに重点の問い/実験中を閲覧専用カード表示（reflect_focus_v1参照・空なら非表示）＋参謀提案のR系実験（Lecticaマスタ外）受け入れ | ✅実装済み 2026-08-18 |
| [taskos-fallback-race修正依頼書.md](specs/taskos-fallback-race修正依頼書.md) | Lecticaフォールバック（ランダム）とCowork提案の競争解消（案A=同期時にrandom由来Shotを提案で置き換え） | ✅既存実装で充足（`3749e36`+`8aa6b86`が案Aと同挙動。08/19朝の事象タイムラインを再現し受け入れ3件PASS。事象は旧ビルド＝R系マスタ外不採用が原因。由来フラグは'cowork'でなく既存'sanbo'を継続） |
| [claude-code-hitomemo-people-file-split-spec.md](specs/claude-code-hitomemo-people-file-split-spec.md) | ヒトメモ取り込みを人物(daily-people)/接点(daily-contacts)の2ファイルに分離。冪等キーをファイル別化し人物ファイルが接点の影に隠れて読まれない問題を解消（両方Cowork出力・読み取り専用のまま） | ✅実装済み 2026-08-19 |
| [claude-code-lectica-random-removal-and-full-memo-spec.md](specs/claude-code-lectica-random-removal-and-full-memo-spec.md) | Lecticaランダム生成を完全廃止（提案が無い日は出さない）・R系(マスタ外)受け入れ・done時も別ID提案は新規追加・Shotカードに実験内容フル表示・完了✔に確認ダイアログ | ✅実装済み 2026-08-20 |
| [reflect-os-idb-stores-実装依頼書.md](specs/reflect-os-idb-stores-実装依頼書.md) | Reflect OSに questions/experiments ストア追加＋Q###/R###連番ID＋初回シード＋バックアップ出力（Brief追補D用） | ⚠️要設計調整（前提が現行実装と不一致：ストアは探求ボードで実装済み・現行はlocalStorage reflectOS_v1・実ギャップはtask-osバックアップの4ストア固定とID規約。実装保留） |
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
