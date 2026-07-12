> ✅ 実装済み 2026-07-13 ・ b8df725（HOMEの3セクション＋デッドコード撤去。autoGenLecticaShot等は存続）

# Claude Code 実装依頼書：Task OS HOMEの重複3セクションを撤去

## 背景
ランチャーOS（統合コックピット）の「今日」タブができ、Morning Briefにも情報が組み込まれたため、
Task OS HOMEにある以下3セクションが重複・不要になった。

## 変更対象
task-os/index.html のHOME画面のみ。他の機能・データは無改変。

## 撤去する3セクション
1. **▶ 今日のLECTICA実験**（HOMEのLectica実験ウィジェット一式：今日のShot/実験中/参謀提案/＋Shotに追加ボタン等）
   - ※Lectica機能自体はReflect OS・ランチャー今日タブにあるため、Task OS HOMEからの表示のみ撤去。
2. **≡ 100リスト — 期限切れ・当月**（HOMEの100リスト表示ブロック）
3. **◈ PROJECT — 直近30日**（HOMEのProject表示ブロック）

## 実装
- 上記3ブロックのHTML描画と、それ専用の生成関数・呼び出しを撤去する。
- 3ブロックが読んでいたデータ（lectica系・100list・project）を、他のHOME要素が使っていないか確認し、
  使っていなければ関連の未使用コードも撤去（デッドコードを残さない）。他で使っていれば関数は残す。
- HOMEの残る要素（VISION表示／今やる／統計カード／各OSへの導線等）は無改変。
- 撤去後、HOMEのレイアウトに不自然な空白が残らないよう整える。

## やらないこと
- Reflect OS・ランチャー・各OS本体のLectica/100list/project機能は一切触らない（Task OS HOMEの表示だけ撤去）。
- GDrive同期・AIタスク読込・バックアップは無改変。

## 検証
- node --check（pre-commit）
- Task OS HOMEから3セクションが消え、レイアウトが整っている
- 残るHOME機能（今やる・統計・導線・VISION）が正常動作
- 撤去したブロック由来のJSエラー・未定義参照が出ない（コンソール確認）
- ランチャー今日タブ側のLectica/100/Project表示は無影響（別ファイルなので当然だが一応確認）

## コミット
「task-os: HOMEの重複3セクション（今日のLectica実験・100リスト期限切れ当月・PROJECT直近30日）を撤去。
ランチャー今日タブとMorning Briefへの移行に伴う整理。デッドコードも除去」
