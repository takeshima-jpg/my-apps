> ✅ 実装済み 2026-07-13 ・ 3217981（Lectica全文表示＋Shot追加/壁打ちコピー/Reflect記録の動線。取り込み本体はReflect/Task OSに委任）

# Claude Code 実装依頼書：ランチャー今日タブ Lectica の全文表示＋取り込み動線

## 背景
ランチャー今日タブのLectica表示が「実験名1行＋→Reftタブ」だけで、実験の詳細（使う場面・選定理由・
完了条件など）が見えない。また壁打ち/取り込みをランチャーから始めたい。

## 変更対象
launcher/index.html のみ。renderTodayLectica（626行付近）を拡張。既存の各OS・Reflectは無改変。

## 1. Lectica実験の全文表示
`aix_lectica_pending`（date=今日のもの）から、実験名だけでなく詳細を展開表示する：
- 実験ID・実験名
- カテゴリ（category）
- 使う場面（targetSchedule）
- 選定理由（reason）
- 完了条件（completionCondition）
（存在するフィールドだけ表示。無いものは省略。aix_lectica_pending のキー名は Task OSの
 lectica_daily_practice 出力に合わせる：selectedExperimentId/Title, category, reason,
 targetSchedule, completionCondition, shotTask）
- 長い場合に備え、既定は実験名＋使う場面まで、「詳細」で全文展開でもよい（実装しやすい方で）。

## 2. 取り込み・実行の動線をランチャーから
実験カードの下にアクションを並べる（既存の各OSロジックを複製せず、導線＝タブ切替 or 既存機能呼び出し）：
- **「＋ 今日のShotに追加」**：aix_lectica_pending.shotTask を今日のShotとして追加。
  ※今日タブのクイック追加と同じ shot-task-os-v1 への書き込み方式（genUid・10フィールド完全一致）を再利用。
  既に追加済み（同一実験IDのShotが今日ある）なら「追加済み」表示にして二重作成しない。
- **「🥊 壁打ちプロンプトをコピー」**：Lectica壁打ちプロンプト本文をクリップボードにコピー
  （reflect-os の LX_PROMPT_SPARRING と同じ本文。ランチャーにも同じ定数を持たせるか、
   文言が長ければ「Reflectタブで壁打ちプロンプトをコピー」への導線でもよい）。
- **「→ Reflectで記録」**：従来どおり reflect タブへ切替（実行後の取り込み用）。

## 3. 実装上の注意
- Shot追加は shot-task-os の addTask 相当と完全に同じフィールド構成にする（実装前に実コード確認）。
  クイック追加で既に同方式を実装済みのはずなので、それを流用する。
- 二重管理を避ける：Lecticaマスターの更新（実験中への遷移等）はランチャーでは行わず、
  Shot追加とプロンプトコピーまで。実験ステータス管理はReflect OSに委ねる。
- localStorage変更時の再描画（既存の renderToday 再描画トリガーに aix_lectica_pending は既に入っている）を維持。

## 検証
- node --check（pre-commit）
- 今日タブでLectica実験の詳細（場面・理由・完了条件）が表示される
- 「＋今日のShotに追加」で今日のShotが作られ、Shotタブに反映／二重追加されない
- 壁打ちプロンプトコピーが動く（またはReflectへの導線が機能）
- 「→Reflectで記録」でreflectタブに切り替わる
- モバイル幅で崩れない

## コミット
「launcher: 今日タブのLectica実験を全文表示（場面・理由・完了条件）＋Shot追加・壁打ちコピー・
Reflect記録の動線を追加。取り込み本体はReflect/Task OSに委ね二重管理を回避」
