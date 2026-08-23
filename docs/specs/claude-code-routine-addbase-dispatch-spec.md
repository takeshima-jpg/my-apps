# Claude Code 実装依頼書【追補v2】：ルーチン完了時の次回日計算に加算基準ディスパッチを追加

作成日：2026-08-23
前提：本日実装済みの「completeRtをcalcNextRoutineDateに統一」の**追加分**。その実装は正しく、置き換えではない。
対象：`routine-os/index.html` の `doComplete()`、`task-os/index.html` の `completeRt()`（両方・同期契約対象）
作業前に必ず `git pull`。

## 新事実（本日実機で確認・今朝の「見送り」判断を撤回する根拠）

「PL実績記入」（月次・**加算基準=月初から加算(from_ms)・加算タイプ=営業日・例外加算日数=5**）を
Task OSから完了 → 次回が **9/22**（8/22＋1か月）になった。設定どおりなら **9/7**（9月の第5営業日）のはず。

原因：完了経路（doComplete／completeRt）は `calcNextRoutineDate`（サイクルのみ参照）を使い、
**設定を全部見る本物の計算関数 `calcNext`（routine-os 575行付近）を呼んでいない**。
`calcNext` は addBase（from_ms/from_me/from_ys/fixed）・addType（business/calendar）・
addDays（例外加算日数）・祝日/週末除外まで実装済みだが、プレビュー用途にしか使われていない。

今朝は「from_last設定=0件のため本家改修見送り」としたが、**from_ms設定が2件実在**
（PL実績記入・経営計画推移表(役員用)、いずれも月次経理系）し、毎月ずれる実害があるため撤回する。

## 修正内容：完了時の計算を addBase でディスパッチする

`doComplete`（routine-os）と `completeRt`（task-os）の次回日計算を、共通の判定に変える：

| t.addBase | 完了時の計算 | 基準日 |
|---|---|---|
| `from_ms` / `from_me` / `from_ys` / `fixed` | **`calcNext(t, base)`** | base＝旧nextDate（期日切れならその過去日） |
| `from_next`（既定・54件） | **現行どおり `calcNextRoutineDate(t, 旧nextDate)`** | 変更しない（今朝の実装を維持） |
| `from_last` | `calcNext(t, 今日)` | 完了日基準（現在0件だが意味を定義） |
| 未設定/不明値 | `calcNextRoutineDate`（現行） | 後方互換 |

### キャッチアップ【必須】
`calcNext` の結果が今日以前になる場合（長期の期日切れ後など）、**結果を新たな基準日として
`calcNext` を再適用**し、未来日になるまで繰り返す（guard 240回・calcNextRoutineDateと同じ思想）。
from_ms なら「翌月の第N営業日」が今日以前 → さらに翌月、と進む。

### 計算不能時
`calcNext` が null（設定不備）を返した場合は、`calcNextRoutineDate` に**フォールバックせず**、
本日実装済みの「上書きしない＋警告」と同じ扱いにする（誤った日付を静かに書かない）。

### Task OSへの移植【同期契約】
`calcNext` とその依存関数（`addBD`／`addCD`／`nBD`／`nLBD`／`isWE`／`isHol`／`ds`／`isValidDate` 等、
routine-os 560〜592行付近）を task-os に移植する。本日と同じ**同期コメント契約**を両ファイルに張ること：
`// ※routine-os/index.html の同名関数と同一実装。変更時は両方を同時に更新すること`
- 祝日データは localStorage `routineOS_holidays` を読む（同一オリジンなのでtask-osからも読める）。
  `isHol` が祝日リストをどのキー/形式で参照しているか routine-os 側を確認し、同じ参照にする
- 名前衝突があれば本日の方式に合わせてプレフィックス改名（routine-os側は変えない）

## 変更しないこと【厳守】
- from_next（54件）の挙動——今朝実装した「サイクル＋曜日保持＋キャッチアップ」のまま
- postponeRt／postponeSh／completeSh
- addRtLog／addLog のログ形式（newNextDate に正しい値が入ることは検証する）
- `calcNext` 本体のロジック（移植はするが改変しない。プレビュー用途との整合を保つ）

## 検証
- 構文検証（node --check）task-os・routine-os 両方
- **PL実績記入ケース**：from_ms・business・addDays=5・旧nextDate=2026-08-22 を完了
  → 次回 **2026-09-07**（9月: 9/1火〜9/4金=4営業日、9/7月=5営業日目）。Routine OS・Task OS両方で同値
- 経営計画推移表ケース：from_ms・business・addDays=6・旧nextDate=2026-08-21 を完了 → 次回 **2026-09-08**
- from_ms・旧nextDateが3か月前 → キャッチアップで「来月以降の直近の第N営業日」になる（過去日にならない）
- 祝日を跨ぐ月（例：9月の敬老の日9/21・秋分を含む下旬設定）で祝日除外が効く（nBDにehが渡ること）
- from_next の週次ルーチン → 今朝の検証と同じ結果（挙動が変わっていないこと）【リグレッション】
- fixed（指定月日固定）→ calcNextの既存ロジックどおり翌年繰り上げが効く
- 設定不備 → 上書きされず警告
- Routine OSから完了した場合とTask OSから完了した場合で**完全に同一の次回日**になる

## コミット
「routine-os/task-os: ルーチン完了時の次回日計算をaddBaseでディスパッチ。from_ms/from_me/from_ys/fixedは
calcNext（営業日・例外加算日数・祝日除外を尊重）＋キャッチアップ、from_nextは現行のサイクル計算を維持。
完了経路で加算基準設定が無視されていた問題を解消（PL実績記入 8/22完了→9/22 が 9/7 になる）」

## 報告
両ファイルの変更箇所／移植した関数一覧／isHolの祝日参照方法／検証結果
（特にPL実績記入=9/7・経営計画推移表=9/8・from_nextリグレッション）。実装を止める場合のみ質問を1つ。
