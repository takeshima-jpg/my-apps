> ✅ 実装済み 2026-07-13 ・ ed3f6b6（toggleSidebar/closeSidebar未定義を実装。欠落はtask-osのみ）

# Claude Code 緊急修正依頼書：Task OS スマホでハンバーガーメニューが開かない

## バグ
スマホでTask OSの右上ハンバーガー（☰）をタップしてもサイドバーが開かない。
→ サイドバーが開けないため「☁️ GDrive接続」ボタンに到達できず、スマホでGDriveログインできない。

## 原因
ボタンは `<button class="mob-menu-btn" onclick="toggleSidebar()">☰</button>`（305行）だが、
**`toggleSidebar()` 関数が定義されていない**（コード内に該当関数が存在しない）。
同様に overlay の `onclick="closeSidebar()"`（302行）の `closeSidebar()` も未定義の可能性。
CSSは用意済み（`.sidebar.open{left:0}` / `.sidebar-overlay.open{display:block}`・680px以下でfixed）。
＝関数だけが欠落した潜在バグ。スマホでしか使わないため露見していなかった。

## 修正
1. `toggleSidebar()` を定義：
   - `.sidebar` に `open` クラスをトグル、`.sidebar-overlay`（#sbOverlay）にも `open` クラスをトグル。
2. `closeSidebar()` を定義：
   - `.sidebar` と `#sbOverlay` から `open` クラスを外す。
3. サイドバー内の項目（各OSリンク・GDrive接続ボタン等）をタップしたら closeSidebar() が走るとなお良い（任意）。
4. 他OS（1day/reflect等）に同じ mob-menu-btn パターンがあり同様に関数欠落していないか確認。
   Task OS以外でも同じ症状があれば同様に修正（今回はTask OS優先）。

## 検証
- node --check（pre-commit）
- スマホ幅（680px以下）で☰タップ→サイドバーがスライドイン、オーバーレイ表示。
  オーバーレイまたは項目タップで閉じる。
- サイドバーの「☁️ GDrive接続」に到達できる。
- PC幅ではサイドバーは常時表示のまま（従来どおり・影響なし）。

## 補足（スマホGDriveログインの動線・関連）
サイドバーが開けば「☁️ GDrive接続」→Googleログインが可能になる想定。
もしタップしてもGoogleログイン画面が出ない場合は、スマホのポップアップブロック、または
OAuthのポップアップ/リダイレクトがモバイルで機能していない可能性。その場合は別途調査するので、
まずサイドバーが開くようにするのが最優先。

## コミット
「task-os: スマホでハンバーガーメニューが開かない不具合を修正（toggleSidebar/closeSidebar未定義を実装）。
サイドバーが開けずGDrive接続に到達できなかった問題を解消」
