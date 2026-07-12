# my-apps 保守ルール（竹嶋OS）

## アーキテクチャ原則（設計憲章 v2.0 抜粋）
- 各OSは単一HTMLファイル完結（vanilla JS・依存ゼロ・ローカルファースト）
- signal over noise：機能を足すより情報を減らす編集を優先
- 削除ではなくアーカイブ。親子階層と空間配置で関係を表現
- 静かなUI・余白。VISION（守りの総合支援を通して、挑戦する人が成長できる社会をつくる）を埋め込む

## 編集ルール
- main直コミット可だが、変更は必ず検証後（下記）。大きな変更はブランチを切る
- コミットメッセージは日本語で「どのOS: 何をなぜ」形式
- ファイル構成：<os名>/index.html（os名: task-os, shot-task-os, routine-os, project-os,
  reflect-os, 1day, brief-viewer, koso-log, 100list, social-universe, hitomemo, launcher）
- 設計・実装依頼書は docs/specs、壁打ち・Coworkプロンプトは docs/prompts を参照（一覧は docs/README.md）
- 「inboxを振り分けて」と言われたら docs/specs/claude-code-minutes-triage-spec.md の手順に従う（inbox/ を読み outputs/triage-YYYY-MM-DD.md を出力。どのOSにも自動書き込みしない）
- シート更新は docs/specs/claude-code-sheets-integration-spec.md の手順に従う（書き込み前バックアップ＋差分承認必須。台帳は docs/sheets.md / docs/sheets.local.md）

## 検証（コミット前に必須）
- vanilla JS のOS：<script>（src無し）を連結して `node --check`
- hitomemo（React/JSX, type="text/babel"）：esbuild --jsx=transform で構文検証
- pre-commit hook（tools/pre-commit）が自動実行する。hookを外さない

## 復元ガード（2026-07 1day巻き戻り事故の再発防止）
- 復元（読込）系の操作にはすべて鮮度比較ダイアログ＋直前スナップショットを付ける。
  新規に復元機能を作る場合も同様。保存はいつでも可、復元は壊れたときだけ
- 実装は各OS共通の rgConfirm / rgSnapshot / rgShowUndo / rgUndo パターン（1day/index.html が参照実装）。
  退避キーは `<os>_pre_restore_snapshot`（1世代）＋JSON自動ダウンロード
- 正本は Task OS の統合バックアップ（myapps-all-backup）。個別GDriveバックアップは復活させない。
  JSON保存（エクスポート）は全OS存続、JSON読込は「詳細（復旧用）」折りたたみ内に置く

## GDrive実装 共通注意（新OSへコピー時必読）
- gdriveLoad後は save() でなく saveData()/saveReviews() を呼ぶ
- gdriveFindFile() のURLは GDRIVE_FILE_NAME 定数を参照（直書きNG）
- チェックリスト: GDRIVE_FILE_NAME変更 / 定数参照確認 / DB_KEY変更 / RV_KEY変更 /
  CLIENT_ID確認 / リダイレクトURI登録確認 / gdriveLoad保存呼び出し確認

## データ契約（壊してはいけないlocalStorageキー）
shot-task-os-v1 / routineOS_tasks / routineOS_logs / routineOS_holidays / pos_v4 /
yaritai_items_v4 / oneday_logs_v1 / oneday_reviews_v1 / kouso_backlog_v1 / kouso_archive_v1 /
su-v6-persons / hitomemo_profiles_v1 / lectica_experiments_master_v1 / lectica_experiment_logs_v1 /
aix_draft_latest / aix_review_weekly / aix_review_monthly / aix_imported_keys / aix_lectica_pending /
hitomemo_aix_imported / taskos_last_sync

## 日次briefの契約
- brief は markdown文字列（aix-tasks.json の brief キー / aix_draft_latest.json）
- lectica_daily_practice は aix-tasks.json のトップレベルJSONキー
- 見出し語（予定/要点/内省/財務・外部/事業・実行/人材・関係/参謀・運用）は色分けに使うため変更禁止

## 人物データ
- id生成は genUid()（Date.now()単独禁止：ID衝突で削除事故の前科あり）
- 名前照合は lxNormName()（括弧注記・空白・NFKC正規化）を必ず使う
- 経営パートナーの関係ステージは docs/partner-stage-legend-v1-1.md を参照（正本）

## build版番号
- task-os の BUILD_VER をUI変更時に当日日付へ更新する
