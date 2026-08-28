# Claude Code 実装依頼書：探求ボードのR系連動（Cowork FB追補J対応）

作成日：2026-08-25
作業前に必ず `git pull`。

## 背景
R系実験（Cowork統合棚卸しの採番：R001等）をReflectのLecticaタブで取り込んでも、
探求ボード（重点の問い・実験中カード）の更新日・実践記録が動かない。
原因＝探求ボードの実験レコードがR系IDを持っておらず、取り込みと紐づかないため。
本改修で「L系もR系も、取り込めば両方更新される」状態にする。

## 作業1：reflect-os（設計チャットで実装・検証済み → 無改変配置）
添付 `reflect-os-index.html` を `reflect-os/index.html` へ**無改変で配置**。
配置前に reflect-os に未取り込みの他変更が無いか差分確認だけすること。

実装済みの内容（参考・変更不要）：
- 実験の追加/編集フォームに「実験ID（R系・任意）」欄を追加
  （形式 R+数字1〜3桁のみ許容・他実験との重複はブロック・決定検証フォームには出さない）
- Lecticaタブの取り込み時、experimentId / relatedExperimentId のR系IDと一致する
  extId を持つ探求ボード実験の practiceCount / lastPracticeDate / updatedAt を進め、
  親の問い（questionId）の updatedAt も進める（＝カードの「更新：」が動く）
- 実験カードに [R001] バッジと「実践n回・最終 YYYY-MM-DD」を表示
- extId 未割当のR系取り込みは従来どおりログのみ（何も壊れない）
- playwright検証PASS：R主実験連動／L主+関連R連動（ログ1件のまま加算）／
  未割当R系の取込継続／リロード永続化

## 作業2：task-os のバックアップ収集対象を拡張（差分適用・2箇所のみ）
`task-os/index.html` に addBase 追補v2 依頼書が別途保留中のため、
**ファイル差し替えではなく以下の2行だけを変更**すること。

### 変更1（837行付近）
```js
// 変更前
const REFLECT_STORES = ['logs','themes','settings','checks'];
// 変更後
const REFLECT_STORES = ['logs','themes','settings','checks','questions','experiments','principles'];
```

### 変更2（restoreReflectIDB 内・852行付近）
```js
// 変更前
['logs','themes','settings','checks'].forEach(s => { if(!Array.isArray(cur[s])) cur[s] = []; });
// 変更後
REFLECT_STORES.forEach(s => { if(!Array.isArray(cur[s])) cur[s] = []; });
```

補足：dump/restore/trimは {version,stores} 形式のまま。trimReflectIDBLogs は
logs だけを絞る実装なので questions/experiments は全量が毎朝のバックアップに載る
（件数が小さいため問題なし）。過去のバックアップ（questions等が無い）の復元は
restoreReflectIDB が Object.keys(dump.stores) で回すため互換（欠けたストアは現状維持）。

## 変更しないこと【厳守】
- reflect-os は添付の無改変配置のみ（追加修正しない）
- task-os は上記2行以外に触れない（addBase保留中のため）
- バックアップの他OS収集・週次スナップショット・復元ダイアログのロジック

## 検証
- 構文チェック（両ファイル）
- task-os でバックアップ実行 → 生成JSONの reflectOS_idb.stores に
  questions / experiments / principles が含まれること
- そのJSONを復元 → Reflect OS の探求ボードに問い・実験が復元されること
- Reflect OS：実験編集で extId=R001 を設定 → LecticaタブでR001取り込み →
  カードの「実践1回・最終日」「更新：」が動くこと

## コミット（2コミット推奨）
1. 「reflect-os: 探求ボード実験にR系ID（extId）を導入し、Lectica取り込み
   （実験ID/関連実験）と連動して実践回数・最終実践日・実験/親の問いの更新日を
   自動更新。カードに[R系ID]バッジと実践回数を表示（Cowork FB追補J）」
2. 「task-os: バックアップのReflect収集対象に questions/experiments/principles
   を追加（探求ボードの二重管理解消・追補J）」

## 報告
両ファイルの配置/変更確認・バックアップJSONへの3ストア追加確認・push完了。
