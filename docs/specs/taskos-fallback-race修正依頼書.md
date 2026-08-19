# CODE修正依頼書：Task OSのLecticaフォールバックとCowork提案の競争を解消する

作成：2026-08-19（Cowork実機で確認した不具合） 対象：`task-os/index.html`（Lectica Shot生成ロジック）

## 事実（2026-08-19 実機）

- 08:35 Task OS起動（バックアップ生成）→ この時点でDriveのdaily-tasks.jsonは前日分（date=2026-08-18）→「今日の提案なし」と判定され、**フォールバックのランダム選定が即時発動**（L051のShotを生成）  
- 08:41 Coworkがrunnowで当日分（R003・date=2026-08-19）を10\_日次データに保存  
- 09:02 GDrive同期 → R003提案を受信したが、**当日のLectica Shotが既に存在するためスキップ**（画面はL051のまま。ランチャーOS＝Brief本文はR003で、本文↔JSONは一致している）

## 構造的な問題

バックアップはTask OSを開かないと作れない → 開いた瞬間にフォールバックが走る → Cowork提案（runnowの出力）は**必ず後から**届く。この順序では、フォールバックの「降格」（2026-08-18改修）だけでは毎朝ランダムが先勝ちする。

## 修正案（どちらか。Aを推奨）

### 案A【推奨】：同期時にCowork提案でフォールバックShotを置き換える

GDrive同期で当日の `lectica_daily_practice` を受信したとき：

1. 当日のLectica Shot（category='Lectica'・dueDate=当日）を探す  
2. 見つかったShotが**フォールバック由来**（lecticaSource==='random' 等のフラグで判別）かつ**未完了**なら、提案内容（experimentId・title・memo）で**置き換える**  
3. 竹嶋さんが手で完了済み（done）にしたShotは置き換えない  
4. Cowork由来のShotが既に一致していれば何もしない（冪等）

※フォールバック生成時に `lecticaSource: 'random'` を必ず付与しておく（既存仕様のまま）。Cowork提案から作るShotには `lecticaSource: 'cowork'` を付与し、判別可能にする。

### 案B：フォールバックの発動を遅延させる

起動時には生成せず、「GDrive同期を1回実行した後もなお当日提案が無い場合」に限りフォールバック生成する。 （欠点：同期しない日はLecticaが出ない。案Aの方が安全）

## 受け入れ確認

1. Task OS起動（提案なし）→ ランダムShot生成 → その後Coworkが当日提案を保存 → GDrive同期 → **Shotが提案内容に置き換わっている**  
2. 提案と同一のShotが既にある状態で同期 → 重複生成されない  
3. ランダムShotを完了済みにした後に同期 → 置き換えられない（完了実績を尊重）

## 応急運用（改修まで）

朝イチのランダムShotは削除してから「GDrive同期」を再実行すると、Cowork提案（当日分保存済みの場合）でShotが立つ。  
