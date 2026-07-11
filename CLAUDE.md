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
- 「inboxを振り分けて」と言われたら docs/claude-code-minutes-triage-spec.md の手順に従う（inbox/ を読み outputs/triage-YYYY-MM-DD.md を出力。どのOSにも自動書き込みしない）
- シート更新は docs/claude-code-sheets-integration-spec.md の手順に従う（書き込み前バックアップ＋差分承認必須。台帳は docs/sheets.md / docs/sheets.local.md）

## 検証（コミット前に必須）
- vanilla JS のOS：<script>（src無し）を連結して `node --check`
- hitomemo（React/JSX, type="text/babel"）：esbuild --jsx=transform で構文検証
- pre-commit hook（tools/pre-commit）が自動実行する。hookを外さない

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

## build版番号
- task-os の BUILD_VER をUI変更時に当日日付へ更新する
