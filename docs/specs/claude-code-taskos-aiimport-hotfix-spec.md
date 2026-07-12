> ✅ 実装済み 2026-07-12 ・ bfec392（genId未定義→共通genUidに統一。error2のdedupe隔離は既存で確認済み）

# Claude Code 緊急修正依頼書：Task OS のAIタスク読込が動かない（genId未定義＋GDrive 403）

今日から Task OS のAIタスク読込・GDrive同期が失敗している。コンソールログに2つのエラー。

## エラー1（本命）：ReferenceError: genId is not defined
```
aix自動取込スキップ ReferenceError: genId is not defined
    at applyAixTasks (index.html:843:37)
    at gdAutoSync (index.html:2343:21)
```
- applyAixTasks（AIタスク取り込み本体）が `genId()` を呼んでいるが未定義。ここで例外→取り込みが丸ごとスキップされている。
- 原因の推定：直近の変更（Shotクイック追加のgenId方式化・コックピット関連）で、Task OS内の
  id生成関数の名前が変わった/削除されたのに、applyAixTasks が古い名前を参照している。
- **調査**：Task OS内のid生成関数の正しい名前を確認（genUid か、shotの genId か、別名か）。
  CLAUDE.mdの「id生成はgenUid()、Date.now()単独禁止」方針に沿って、**正しい共通関数に統一**する。
- **修正**：applyAixTasks 内の genId 呼び出しを、実在する正しいid生成関数に置き換える。
  ついでに Task OS内で id生成関数が複数名で散在していないか確認し、1つに寄せる（重複定義・名前ゆれの解消）。

## エラー2：GDrive 403 Forbidden（trash失敗）
```
trash失敗 aix-tasks.json Error: http 403
    at gdFetch → gdDedupeDrafts → gdAutoSync
```
- gdDedupeDrafts（Drive重複ファイルのゴミ箱移動）がPATCH/trashで403。これは取り込み本体とは別系統だが今日から発生。
- **調査**：
  (a) GDriveトークンのスコープが drive.readonly など**書き込み不可**になっていないか
      （読み取りは通るがPATCH/trashだけ403なら、スコープが読み取り専用の可能性大）。
  (b) 直近コミットで gdDedupeDrafts / gdFetch のリクエスト（メソッド・ヘッダ・fileId）が壊れていないか。
- **修正方針**：
  - スコープが原因なら、GDrive認証のスコープに書き込み（https://www.googleapis.com/auth/drive）が
    含まれるようにし、**トークン再取得を促す導線**（再接続ボタン）を確認/追加。ユーザーは再ログインで直る。
  - リクエスト不備なら該当を修正。
  - **重要**：gdDedupeDrafts が失敗しても**AIタスク取り込み本体は完遂すべき**。dedupe失敗が
    同期全体を止めないよう、dedupeを try/catch で分離し、失敗しても取り込み・保存は続行するようにする
    （掃除は失敗してもデータ取り込みは死守）。

## 検証
- node --check（pre-commit）
- Task OSでGDrive同期→AIタスク読込：例外なくタスクが取り込まれること（今日のbrief・tasksが反映）
- genId参照が解消（コンソールにReferenceErrorが出ない）
- 403が出る場合でも、取り込み本体は完了し today のタスク・briefがlocalStorageに入ること
- 可能なら書き込みスコープでの再接続後に dedupe(trash) も成功すること

## コミット
「task-os: AIタスク読込のgenId未定義を修正（正しいid生成関数に統一）・GDrive dedupe失敗が
同期全体を止めないようtry/catch分離・書き込みスコープ再接続の導線確認。今日発生した取込停止の緊急修正」

## 補足（所有者向け・別件だが関連）
コックピット/Task OSの「AIタスク読込」ボタンがローカルのファイル選択（OneDrive初期表示）を開く不具合は、
docs/claude-code-cockpit-reload-fix-spec.md で修正予定。本体はDriveからの自動取得であるべきで、
手動ファイル選択は廃止方針（未実装なら合わせて対応）。
