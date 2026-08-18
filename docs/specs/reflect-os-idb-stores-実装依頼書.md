# CODE実装依頼書：Reflect OSに questions / experiments ストアを追加（IndexedDB）

作成：2026-08-18（メンテナンスチャット設計 → CODE実装用）
対象：`reflect-os/index.html`（単一HTML・IndexedDB）
目的：Morning Brief（Cowork）が `reflectOS_idb.stores.questions / experiments` を読んで「重点の問い」1行とR系実験の日次出題を行えるようにする（Brief追補D・2026-08-18）。

---

## 1. スキーマ追加

IndexedDBのバージョンを +1 し、`onupgradeneeded` で以下2ストアを新設する。

### questions（keyPath: 'id'）
```json
{
  "id": "Q001",
  "text": "相手の人生と会社の未来をどう接続し、人生応援と経営責任を両立するか？",
  "status": "focus",            // 'focus' | 'archived'
  "createdAt": "…", "updatedAt": "…"
}
```

### experiments（keyPath: 'id'）
```json
{
  "id": "R001",
  "title": "問いを一緒に開き、自分も一手動く",
  "description": "問いを置いたら観察に回るのではなく、自分の一手（試作・下書き・最初の1行）も同じ場に差し出し、相手の一手と並べて創る。",
  "completionCondition": "問いを置いた場で自分の一手も1つ差し出し、相手の次の一手を確認した。",
  "status": "active",           // 'active' | 'completed' | 'skipped'
  "createdAt": "…", "updatedAt": "…"
}
```

- IDは `Q###` / `R###` の連番。CoworkはこのIDをBrief本文と `lectica_daily_practice.experimentId` の両方に使う（ID完全一致規約・追補A）。

## 2. 初回シード（既存データからの移行）

新ストアが空のとき、localStorage `reflectOS_v1` から1回だけ移行する：

- `importantQuestions`（3件・2026-07-19）→ Q001〜Q003、status='focus'
- `activeExperiments`（3件・2026-07-19）→ R001〜R003、status='active'
- **R001はシード時に補正文言へ差し替える（竹嶋2026-08-16承認済み）**：
  - 旧：「問いを渡して自走を観察する」
  - 新：title「問いを一緒に開き、自分も一手動く」＋上記description/completionCondition
- R002「未来接続型の対話を行う」／R003「問題を構造で捉える」は文言そのまま（completionConditionはLectica×Reflect統合棚卸し_2026-08-17.mdの変換を採用してよい）
- 移行済みフラグを settings ストアに記録し、二重シードを防ぐ

## 3. UI（最低限）

- questions：status切替（focus⇄archived）、text編集、追加
- experiments：status切替（active／completed／skipped）、title・completionCondition編集、追加
- 既存の壁打ち取込（parseAiReflect）で【問い】【次の実験】が来た場合の新規登録は任意（第2段でよい）

## 4. バックアップ出力

- `myappsallbackup` 生成時の `reflectOS_idb.stores` エクスポートが**ストア名を動的列挙**していれば追加作業なし
- ハードコードの場合は `questions` / `experiments` を追記
- 受け入れ確認：バックアップJSONで `reflectOS_idb.stores.questions`（focus 3件）と `stores.experiments`（active 3件・R001が補正文言）が出力されること

## 5. Cowork側の挙動（参考・実装不要）

- 新ストアが現れるまで：旧 `reflectOS.importantQuestions` / `activeExperiments` をフォールバック読みし、同ルールで出題
- 新ストア検出後：`status==='focus'` の問いから「・重点の問い：」を最大1行、`status==='active'` の実験（R系）をL系と同列で日次選定。R系選定日も `lectica_daily_practice` を必ず出力（experimentId=R系ID）
