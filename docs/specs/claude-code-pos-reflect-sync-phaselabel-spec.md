# Claude Code 実装依頼書：Project OS × Reflect OS 同期の正本化と「フェーズ／テーマ」ラベル

作成日：2026-09-27／起案：設計チャット（竹嶋さんのメンテナンス依頼を実コードで検証済み）
対象：`reflect-os/index.html`・`project-os/index.html`・`task-os/index.html`（小修正1点）
土台：main（bda383c）。作業前に必ず `git pull` し、HEADを確認すること。**1施策＝1コミット**。

---

## 0. 実コードで確認した事実（参謀の見立てとの差分）

依頼の前提のうち2点は、実コードでは状況が異なる。以下を正として実装すること。

**(a) Reflect OS の二重管理は存在しない。正本は localStorage `reflectOS_v1` 一本。**
- Reflect OS の永続化は `reflectOS_v1` のみ（旧IndexedDB `ReflectOS7` は初回に一度だけ移行して以後未使用）。
- バックアップの `reflectOS_idb` は名前に反して IndexedDB ではなく、Task OS の `dumpReflectIDB()` が **`reflectOS_v1` の全内容を `{version, stores}` 形式で書き出したもの**（＝正本の全量。themes 14件）。
- バックアップの `reflectOS`（v1）は別ストアではなく、Task OS の `readReflectOSFromIDB()` が作る **Cowork向け要約**。`status!=='完了'` のテーマだけを `{title, status, priority, question, hypothesis}` に写したもの。だから id が無く件数も少ない（前田さんPJは9/27に完了＝除外）。
- → 反映先は `reflectOS_v1` だけでよい。要約側は正本から毎回再生成される。

**(b) 名前変更はすでに運ばれる設計。未反映に見えるのは「Reflectを開くまで同期が走らない」ため。**
- `syncFromProjectOS()` は Reflect 起動時（`boot()`）と「↺ PJ同期」ボタンで実行される。
- このとき `title / status / priority / goal / badFuture / successConditions / nextMove` は **既にPJ値で毎回上書き**している（`{...already, ...mapped}`）。「空欄補完のみ」なのは `currentState`（問い）と `summary`（仮説＝センターピン）の2つだけ。
- Project由来テーマ（`_fromProjectOS:true`）はReflect画面に編集ボタンが無く、手入力で書き換える経路は無い。
- → 9/27にCoworkが `pos_v4` を直接書き換えた後、Reflect を一度開けば `pos_s6n9vf1vgdx` の title は「3Aグループ2030構想」になるはず。実装前に**現状のままでそうなるかを先に確認**し、報告に記載すること。

**(c) Project OS の画面表示はすでに全PJ「重点テーマ」になっている。**
- 詳細の見立てブロック・詳細メタ・ホームカードとも、`phases` のラベルは「重点テーマ／テーマ」（8月の改修で「重点テーマはフェーズではない」として変更済み）。
- 壁打ちコンテキスト（`sparkCopy`）と共有用エクスポート（`shareModal`）には `phases` 自体が出力されていない。
- 「フェーズ」と呼ばれているのは、`pos_v4` のキー名（`phases`/`phase`）とシート由来の「フェーズマップ」を Cowork が読んでいるため。
- → ラベルを PJ ごとのデータとして `pos_v4` に持たせれば、画面と Cowork の両方で呼び方を揃えられる。

---

## 施策1：Project OS を正として Reflect に反映する（reflect-os）

### 方式の提案：自動（現行方式を拡張）。確認ダイアログは入れない
- 同期はすでに自動（Reflect 起動時）。穴は「Reflect を開いている間に Project OS が変わった場合」と「センターピンが空欄補完のみ」の2点だけなので、そこを塞ぐ。
- Project OS 保存時の「Reflectにも反映しますか？」は、催促・確認を増やさない方針（v2.1）に反するうえ、他アプリの localStorage へ書き込む経路を新たに作ることになるので採らない。

### 1-A. 同期対象にセンターピンを追加（PJ正で毎回上書き）
- `mapped` に `centerPin: p.centerPin || ''` を追加する（**新フィールド**。既存の `summary` は触らない＝既存値を消さない）。
- テーマカードの「現在の仮説（センターピン）」表示を、Project由来テーマでは `t.centerPin || t.summary` にする。
- `currentState`（問い）は従来どおり空欄補完のまま（依頼の上書き対象に「問い」は含まれないため）。

### 1-B. Reflect を開いている間も追随する
- 既存の `storage` イベントリスナー（`reflectOS_v1` 変更時に reload している箇所）に `pos_v4` を追加し、変更時は `syncFromProjectOS()` → テーマ再読込 → `ra()` を実行する（reload はしない。入力中のフォームを壊さないため）。

### 1-C. 触らないもの（厳守）
- Reflect 側の問い・実験・ログ・原則（`questions/experiments/logs/principles/checks`）。
- `_fromProjectOS:false` のテーマ（手動テーマ）。`pos_1uip87uw9k4`（竹嶋家100年の計）は対応PJが消えたため既存ロジックで手動テーマ化されたもの。現状維持。
- 対応PJが無くなったテーマを消さない既存挙動。

### 1-D. 付随修正（task-os・1行）：Cowork 向け要約のフィールド取り違え
- `readReflectOSFromIDB()` の themes 写像が、テーマに存在しない `t.question / t.hypothesis` を読んでいるため、要約の問い・仮説が常に空になっている。
- 次に置き換える（キー名は Cowork 互換のため維持し、値の取り先だけ直す。id と由来を追加）：
  `{ id: t.id||'', title, status, priority, question: t.currentState||'', hypothesis: t.centerPin||t.summary||'', fromProjectOS: !!t._fromProjectOS }`

### 検証（施策1）
1. 実装前：現行コードのまま、`pos_v4` の該当PJ名を変更 → Reflect を開く → `pos_s6n9vf1vgdx` の title が追随するか（事実確認として報告）。
2. 実装後：`pos_v4` の name / goal / centerPin / badFuture / successConditions / nextMove を変更 → Reflect 起動で全項目が反映。
3. Reflect を開いたまま別タブで Project OS を保存 → リロード無しでテーマが更新される。
4. `summary` / `currentState` に既存値があるテーマで、既存値が消えていない。手動テーマ・問い・実験・ログが無変更。
5. `readReflectOSFromIDB()` の出力で question / hypothesis が埋まる。
6. 最終確認：実データ相当で `pos_s6n9vf1vgdx` の title が「3Aグループ2030構想」。

---

## 施策2：PJごとに「フェーズ／テーマ」を選べる（project-os）

### 2-A. データ
- PJ に `phaseLabel: 'phase' | 'theme'` を追加（任意フィールド。**未設定＝'phase'**）。`phases` の中身は変えない。
- 表示用ヘルパーを1つ作る：`phaseWord(p)` → `'theme'` なら「重点テーマ」、それ以外は「フェーズ」。短縮形（ホームカード用）は「テーマ」／「フェーズ」。

### 2-B. 表示の切替箇所（現在「重点テーマ」固定の3か所）
- 詳細の見立てブロックの見出し（`ov-section-lbl`「重点テーマ」）
- 詳細メタ折りたたみの summary「詳細メタ（重点テーマ・PJ設定）」とその中の見出し
- ホームカードの現在地表示（「テーマ n …」）
- ※ 既定を「フェーズ」にするので、`phaseLabel` 未設定のPJは表示が「重点テーマ」→「フェーズ」に変わる。これは依頼どおり（前田さんPJのような段階型が既定）。

### 2-C. 編集フォーム
- `openProjModal` に「重点項目の呼び方」セレクト（フェーズ＝順番に進む段階／テーマ＝並列の重点）を追加し保存。

### 2-D. 壁打ち・共有
- `sparkCopy` / `shareModal` には現状 `phases` が出力されていないため変更不要。将来出力する場合は `phaseWord(p)` を使うこと（コメントで残す）。

### 2-E. 既存データの移行
- 移行前に `pos_v4` を `pos_backup_phaselabel_20260927` に退避（既に同名キーがあれば上書きしない）。
- `s6n9vf1vgdx`（3Aグループ2030構想）に `phaseLabel:'theme'` を一度だけ設定（冪等。既に値があれば触らない）。他PJは未設定のまま。

### 検証（施策2）
1. 3Aグループ2030構想：詳細・メタ・ホームカードが「重点テーマ／テーマ」。
2. 他PJ（phaseLabel 未設定）：「フェーズ」表示。
3. 編集フォームで切り替え → 保存 → 表示が切り替わり、`phases` の中身は無変更。
4. 退避キー `pos_backup_phaselabel_20260927` が作られ、移行が2回目以降は何もしない。
5. 催促・アラート・確認ダイアログが増えていない。

---

## Cowork への申し送り（竹嶋さん経由・実装とは別）
- `pos_v4` の各PJにある `phaseLabel` を見て、`phases` を「フェーズ」または「重点テーマ」と呼び分けること（未設定＝フェーズ）。3Aグループ2030構想は「重点テーマ」。
- Reflect の正本は `reflectOS_v1`（バックアップの `reflectOS_idb.stores`）。バックアップの `reflectOS` は要約であり、件数が少ないのは完了テーマを除外しているため。

## コミット案
1. `reflect-os: Project由来テーマにcenterPinをPJ正で同期（summaryは保持）、pos_v4変更をstorageイベントで追随`
2. `task-os: Cowork向けReflect要約のテーマ写像を修正（question←currentState・hypothesis←centerPin/summary、id・fromProjectOSを追加）`
3. `project-os: PJごとに重点項目の呼び方（フェーズ/テーマ）を選べるphaseLabelを追加。既定はフェーズ、3Aグループ2030構想はテーマに移行（pos_backup_phaselabel_20260927へ退避後）`

## 報告に含めること
- 施策1 検証1（実装前の事実確認）の結果
- 各検証項目の結果とスクリーンショット（3Aグループの詳細・前田さんPJの詳細・Reflectのテーマカード）
