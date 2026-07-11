# Claude Code 実装依頼書：コックピット起動時にAIタスクを1日1回自動取り込み

## 目的

毎朝「🤖AIタスク読込」を手で押す工程をなくす。コックピットを開いたら、その日まだ取り込んでいなければ 自動でAIタスク（aix-tasks.json）を取り込む。1日1回だけ。

## 設計原則【重要】

取り込み本体（applyAixTasks：台帳 aix\_imported\_keys の管理、lectica\_daily\_practice処理、 brief/aix\_drafts保存など）は **Task OSにしかない**。これをコックピットに複製すると二重管理になり 事故の温床になる。よって：

- **取り込みロジックはTask OS側に集約したまま**にする  
- コックピットは「1日1回、取り込みが必要か判定し、Task OSに実行させる」司令だけを担う

## 実装方式（安全な非表示iframe方式）

### Task OS側（task-os/index.html）

- URLパラメータ `?autoimport=1` で開かれたら、**GDrive同期→AIタスク読込を1回自動実行し、完了したら postMessageで親（コックピット）に結果（取り込み件数）を通知**する処理を追加。  
  - 既存のGDrive同期・applyAixタスク読込関数をそのまま呼ぶ（新規ロジックを書かない）  
  - GDrive未接続なら「未接続」を親に通知して何もしない  
  - autoimportで開かれた場合のみこの自動実行が走る（通常の直接アクセスは従来どおり無変更）

### コックピット側（launcher/index.html）

- 起動時（「今日」タブ表示時）に、`localStorage['cockpit_last_autoimport']` が今日の日付でなければ：  
  1. 画面外の**非表示iframe**で `task-os/index.html?autoimport=1` を読み込む  
  2. Task OSからのpostMessage（取り込み完了/件数/未接続）を受け取る  
  3. `cockpit_last_autoimport` に今日の日付を記録  
  4. 今日タブのタスク一覧を再読込して反映。小さくトースト「AIタスクを取り込みました（N件）」 ／未接続なら「Googleログインが必要です（🔑ログインから）」  
  - 非表示iframeは完了後に破棄（または再利用）  
- 手動の「🤖AIタスク読込」ボタン（前回追加分）は残す（未接続後の再実行や手動再取り込み用）

## 事故防止の確認

- **二重取り込みしないこと**：applyAixタスクの既存台帳(aix\_imported\_keys)が効くため複数回走っても安全。 加えて cockpit\_last\_autoimport で1日1回に制限（ダブルの防御）  
- postMessageは **origin を検証**する（同一オリジン takeshima-jpg.github.io 以外は無視）  
- autoimport実行は**取り込み（読み取り→localStorage追加）のみ**。復元・全上書き系は一切呼ばない （直近の復元ガード対象操作を自動で走らせないこと）

## 検証

- node \--check（両ファイル・pre-commit）  
- 動作：コックピット初回起動で自動取り込み→今日タブにタスク反映→トースト表示。 同日2回目の起動では自動取り込みが走らない（cockpit\_last\_autoimport 判定）。  
- GDrive未接続時：エラーで止まらず「ログイン必要」案内が出る。  
- Task OSを直接開いた場合（autoimportなし）は従来どおり自動実行が走らない。  
- postMessageのorigin検証が効く（別オリジンからのメッセージを無視）。

## コミット

「launcher/task-os: コックピット起動時のAIタスク自動取り込み（1日1回・非表示iframe＋postMessage方式）。 取り込み本体はTask OSに集約し二重管理を回避。origin検証・台帳・日付ガードの三重防御」  
