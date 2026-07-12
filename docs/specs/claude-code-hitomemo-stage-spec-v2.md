> ✅ 実装済み 2026-07-12 ・ hitomemo=05cffb7 / SU・health=1b78a64（凡例 partner-stage-legend-v1-1 準拠。マイグレーションは所有者承認で実行）

# Claude Code 実装依頼書 v2：ヒトメモ関係ステージ改修（4段階＋稼働フラグ＋周辺追従）

前提：docs/partner-stage-legend-v1-1.md（凡例・正本）を必ず読むこと。
v1からの変更：2段目を「つながり」に／前田特例／SU同期・AI更新パーサ・health checkの追従を追加。

## 変更対象
hitomemo/index.html（主）、social-universe/index.html（同期ボタンの追従のみ）、tools/check_backup_health.py（1項目）。

---

## 1. データモデル（hitomemo_profiles_v1）
- `stage` を関係ステージに再定義：`記録のみ / つながり / 信頼を深める段階 / 経営パートナー` の4値
- `isActive`（boolean）新設：🤝 今この人と仕事が動いている
- 旧 `stage`（知人/協力者/…＝仕事役割）は `roleStage` にリネーム退避（表示は「（参考）仕事役割」）
- 旧 `tier` は移行後に参照を廃止（フィールド自体は残ってよいが、UI・ロジックはstageに一本化）

## 2. マイグレーション（起動時1回・承認つき）
`hitomemo_migrated_stage_v2` 未設定なら、confirmで件数と内訳を提示→承認後に実行。実行前に自動JSONバックアップDL。
- tier='記録のみ' → stage='記録のみ'
- tier='仲間候補' → stage='つながり'
- tier='経営パートナー候補' → stage='つながり', isActive=true
- **特例**：engagementType が「維持（確定パートナー・専門家）」の人物のうち、
  名前が前田（lxNormNameで照合）→ stage='経営パートナー'。
  福山 → stage='つながり'（関わり方タイプ=相互学習のまま・路線外）
- 旧 stage → roleStage へ退避
- 完了トースト：「関係ステージを移行しました（N件）。各人の段階を詳細画面で確認・調整してください」

## 3. UI（hitomemo）
- 詳細画面：stage=4段階セレクト＋ヘルプ（?アイコンで凡例の1行説明）、isActive=「🤝 稼働中」トグル、
  roleStage=小さく参考表示
- 一覧/HOME：ステージ別バッジ（記録のみ=グレー/つながり=青/信頼を深める段階=amber/経営パートナー=緑）＋🤝小アイコン
- HOME進捗バー：stage='経営パートナー' の人数 / 10
- 凡例表示：サイドバーかヘルプに「📖 関係ステージの凡例」を追加し、docs/partner-stage-legend-v1-1.md の
  要点（4段階の意味・路線限定・昇格トリガー・棚卸しルール）を表示

## 4. AI更新読込パーサの追従
- stage の受付値を4段階に更新（旧6値が来たら無視して警告表示）
- `isActive: true/false`（日本語ラベル「稼働中：あり/なし」も可）と `roleStage` の更新に対応
- 既存の lxNormName 照合・複数一致選択・プロフィール9欄上書き・changeLogは無改変

## 5. Social Universe「🤝 ヒトメモで管理」同期の追従【重要：旧tier復活の防止】
- 現在この同期はTop10を基準に旧tierを書き込んでいる。これを廃止し：
  - 新規人物の同期時は stage='記録のみ'（またはヒトメモに既存なら**stageを変更しない**）で作成
  - **既存人物のstage/isActiveを上書きしない**（SUはTop10＝注意配分の軸であり、深さの軸ではない。凡例参照）
  - Top10情報は参考として渡してよい（例：メモやTop10フラグ的な別フィールド）が、stageには触れない

## 6. tools/check_backup_health.py の追従（1項目）
- 「仕組みの空転」チェックの対象を「Top10」から「stage が 信頼を深める段階 または 経営パートナー の人物」に変更
  （nextExperience設定済みで30日ログなし、の母集団を新ステージ基準に）

## 検証
- hitomemo：esbuild --jsx=transform で構文検証。マイグレーションを旧データ一式（tier3種・前田・福山含む）で
  テストし、凡例どおりの結果＋バックアップDL＋1回限りを確認
- SU同期：既存人物のstageが上書きされないこと／新規は記録のみで入ること
- AI更新読込：新stage値・isActive・roleStageの更新、旧6値の警告
- health check：偽データで空転チェックの母集団が新基準になっていること
- 進捗バーが経営パートナー段階のみを数えること（移行直後は前田さんの1/10になるはず）

## コミット（分割可）
「hitomemo: 関係ステージを4段階（記録のみ/つながり/信頼を深める段階/経営パートナー）＋🤝稼働フラグに改修。
旧tier/stageを安全移行（前田特例・バックアップ＋承認）、凡例表示追加」
「social-universe/tools: 新ステージへ追従（SU同期はstageを上書きしない・health check母集団変更）」
