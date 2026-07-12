> ✅ 実装済み 2026-07-12 ・ コミット 89f825e（アイコンはB案・白背景版を所有者選定）

# Claude Code 実装依頼書：launcher（コックピット）のPWA化 ＋ アイコン作成

## 目的
コックピットをPWA化し、スマホ・PCのホーム画面/デスクトップに「アプリ」として追加できるようにする。
アドレスバーの無いstandalone表示で、体感を完全に「1つのアプリ」にする。あわせてファビコン/アプリアイコンを作成。

## 前提・制約
- 単一ファイル完結・依存ゼロの憲章を維持。アイコンは**外部画像を使わずSVGで自作**し、
  必要なPNGサイズはSVGから生成（またはSVGアイコン＋manifestで対応）。
- GitHub Pages（静的ホスティング）で動く構成にする。ビルド不要。
- 対象は launcher/ のみ。他OSは無改変。

## 1. アイコンの作成（SVG）

デザイン案A「操縦席（コックピット）」を採用：
- 背景：角丸スクエア（濃紺 #1E2A44 など静かな濃色）
- 中央から放射する細い線が数本、中心に1つの点（「複数OSが1点に集約」＝統合コックピット）
- 放射線の先端3本だけを既存ソース色（黄緑#8DC63F・緑#3AA655・紫#7C5CD6）で差し色
- signal over noise の思想に沿い、余白を多く・要素は最小限
- maskable対応（安全領域内に主要素を収める。丸型トリミングでも欠けないよう中央に集約）

生成物：
- launcher/icon.svg（マスター）
- launcher/icon-192.png / icon-512.png / icon-maskable-512.png（manifest用。SVGから生成）
- launcher/favicon.svg（ブラウザタブ用。同デザインの簡略版）
- launcher/apple-touch-icon.png（180x180・iOS用）

※ 上記デザインはたたき台。実装時に3案（A操縦席／B集約グリッド／C一点集中）をSVGで作って
　私（所有者）に見せ、選ばせてくれてもよい。迷えばAで進めてよい。

## 2. Web App Manifest（launcher/manifest.webmanifest）
```
{
  "name": "my-apps コックピット",
  "short_name": "コックピット",
  "start_url": ".",
  "scope": ".",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#1E2A44",
  "theme_color": "#1E2A44",
  "icons": [
    {"src":"icon-192.png","sizes":"192x192","type":"image/png"},
    {"src":"icon-512.png","sizes":"512x512","type":"image/png"},
    {"src":"icon-maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}
  ]
}
```
- launcher/index.html の <head> に manifest / theme-color / apple-touch-icon / favicon のリンクを追加。

## 3. Service Worker（最小・慎重に）
**重要**：過去に他OSでSW由来のキャッシュ事故があり、my-appsはSWを無効化してきた経緯がある。
そのためコックピットのSWは以下に限定する：
- **PWAインストール要件を満たすための最小SW**にとどめる
- キャッシュ戦略は **network-first（常にネット優先・失敗時のみキャッシュ）**、または
  キャッシュを一切持たず fetch をそのまま通す「パススルーSW」でよい
- **iframeで読み込む各OSページはSWのスコープ/キャッシュ対象にしない**（launcher/配下のみscope）
  → 各OSが古いキャッシュで表示される事故を絶対に起こさない
- SWのバージョン定数を持ち、更新時に旧キャッシュを確実に破棄する
- 「オフライン動作」は狙わない（目的はホーム追加とstandalone表示。オフラインキャッシュは事故源なので不要）

## 4. インストール導線
- コックピットのヘッダかメニューに「📲 アプリとして追加」ボタンを置き、
  beforeinstallprompt を捕まえて promptを出す（対応ブラウザのみ表示）。
- iOSはbeforeinstallprompt非対応のため、iOS判定時は「共有→ホーム画面に追加」の1行案内を出す。

## 検証
- node --check（pre-commit）
- Chromeのアプリインストール要件（manifest・アイコン・SW・https）を満たし、インストール可能になること
- インストール後、standaloneで起動しアドレスバーが消えること／アイコンが正しく表示されること
- **iframe内の各OSが、SWキャッシュではなく常に最新で表示されること**（network-first検証。
  適当なOSを1行変更→push→コックピット内のそのタブが更新される）
- theme-color がスマホのステータスバーに反映されること

## コミット
「launcher: PWA化（manifest＋最小network-first SW＋自作SVGアイコン）。ホーム追加・standalone表示に対応。
SWスコープはlauncher/配下限定・iframeの各OSはキャッシュ対象外にし過去のキャッシュ事故を回避」
