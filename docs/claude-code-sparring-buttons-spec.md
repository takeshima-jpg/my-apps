# Claude Code 実装依頼書：reflect-os に壁打ちプロンプトのコピーボタンを追加

## 目的
スマホや素のチャットから壁打ちを始めるとき用に、プロンプト本文をワンタップでコピーできるボタンを
reflect-os に追加する（PCではClaudeのプロジェクト機能を使うため、ボタンはモバイル補完の位置づけ）。

## 前提
- docs/ に2ファイルが置いてある：
  - `docs/reflect-sparring-prompt.md`（Reflect壁打ち：内省→記録→行動）
  - `docs/lectica-sparring-prompt.md`（Lectica壁打ち：実験の設計→フィードバック→取り込み）
- reflect-os には既にコピー実装がある：`LX_PROMPT_START` / `LX_PROMPT_SUMMARY` 定数と `lxCopyText(txt, btn)`。
  **同じ方式を踏襲**する（プロンプト本文はPythonで json.dumps したJS文字列リテラルとして定数注入。
  バッククォート等のエスケープ事故防止のため手書き埋め込みはしない）。

## 実装内容（reflect-os/index.html のみ）

### 1. 定数追加（LX_PROMPT_SUMMARY の直後）
- `const RF_PROMPT_SPARRING = <docs/reflect-sparring-prompt.md の全文>;`
- `const LX_PROMPT_SPARRING = <docs/lectica-sparring-prompt.md の全文>;`

### 2. Lecticaタブ：壁打ちボタン追加
- 固定バー内 btnGrp の**左端**（「💬 新規チャット用をコピー」の左）に追加：
  `🥊 壁打ち用をコピー` → `lxCopyText(LX_PROMPT_SPARRING, btn)`
- 既存2ボタンと同じ btn-g スタイル・「✓ コピーしました」フィードバック。

### 3. 「⬇ 取り込む」タブ：Reflect壁打ちボタン追加
- タイトル「⬇ 取り込む」とサブ文の直後、既存の details（AIへの指示プロンプト）の**上**に配置：
  `🥊 壁打ち用をコピー（内省→記録→行動）` → `lxCopyText(RF_PROMPT_SPARRING, btn)`
- 補足の1行を添える（小さめのグレー文字）：
  「新規チャットに貼って壁打ち → 最後に出る【振り返り】ブロックを下のテキストエリアに貼って登録」
- 既存の整形プロンプト details・テキストエリア・登録ボタンは**無改変**。

## 検証
- node --check（pre-commit が走る）
- 両ボタンでコピー内容の先頭・末尾がプロンプト原文と一致すること（コンソールで length 比較でよい）
- 既存ボタン（新規チャット用/まとめ用/貼り付けて取り込む）の動作が変わらないこと

## コミット
「reflect-os: 壁打ちプロンプトのコピーボタンを追加（Lecticaタブ＋取り込むタブ）。モバイルからの壁打ち起動用」
docs/ の2プロンプトも未コミットならあわせて含める。
