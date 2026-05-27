# 自作システム — フォルダ構成

## 起動方法

```bash
cd 自作システム
python -m http.server 8000
```
→ http://localhost:8000/launcher/ を開く

PWAとしてインストール可能（Chrome/Safari のアドレスバーの「インストール」ボタン）

---

## フォルダ一覧

| フォルダ | アプリ名 | 用途 |
|---|---|---|
| `launcher/` | 自作システム Launcher | 全アプリへの入口 |
| `task-os/` | Task OS v5 | ショット・ルーチン・プロジェクト統合 |
| `shot-task-os/` | Shot Task OS | 単発タスク専用 |
| `routine-os/` | Routine OS v2 | ルーティン管理 |
| `project-os/` | Project OS | 経営PJ・分岐点管理 |
| `1day/` | 1day | 日次思考ログ |
| `reflect-os/` | Reflect OS | 内省・気づきログ |
| `koso-log/` | KOSOLog | 施策・行動ログ |
| `100list/` | 100list | やりたいことリスト |
| `social-universe/` | Social Universe | 人間関係マッピング |
| `hitomemo/` | ヒトメモ | 人物プロファイリング |
| `shared/` | 共有素材 | 共通アセット・プロンプト |
| `archive/` | アーカイブ | 旧バージョン保管 |
| `docs/` | ドキュメント | 設計メモなど |

---

## 各フォルダの構造

```
[app]/
├── index.html       ← メインファイル（ここを開く）
├── manifest.json    ← PWA設定
├── service-worker.js← オフライン対応
├── icons/           ← アプリアイコン（icon-192.png, icon-512.png）
├── data/            ← エクスポートデータ置き場
├── backup/          ← バックアップ
└── prompts/         ← Claude用プロンプトメモ
```

---

## PWA化について

各アプリはすでに manifest.json + service-worker.js が入っています。
アイコン画像（icons/icon-192.png と icon-512.png）を用意すると
ホーム画面へのインストールが完全に機能します。

アイコンなしでもインストール自体は可能です。
