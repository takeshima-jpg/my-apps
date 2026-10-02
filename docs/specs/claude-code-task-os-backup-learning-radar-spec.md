# 学びレーダー Phase 2（Claude Code）：統合バックアップ登録とコックピットのカード追加

- 作成日：2026-10-02
- 宛先：Claude Code
- 前提：Phase 1（learning-radar/index.html、コミット 47d1550 以降）が main に入っていること
- 関連：docs/specs/claude-code-learning-radar-spec.md（Phase 1 依頼書）

## 0. 作業前

1. `git pull` し、HEAD が origin/main と一致することを確認
2. task-os/index.html の `collectAllOSData()` / `restoreAllOSData()` と、その対象キー一覧（Shot/Routine/Project/100list/1day/KOSOLog/Social Universe/ヒトメモ）を読む。既存の各 OS がどう追加されているか（キー名・丸ごと格納か配列か・復元時の扱い）を先に確認し、同じ型で足す
3. コックピット（ランチャー OS）の index.html を読み、既存カードの構造（タイトル・説明・リンク・サブ情報の有無）を確認する

## 1. Task OS：統合バックアップに `learningRadar_v1` を追加

- `collectAllOSData()`：localStorage `learningRadar_v1` を JSON.parse し、キー `learningRadar_v1` としてオブジェクトを丸ごと格納する。未作成（null）なら省略（既存 OS の未作成時の扱いに合わせる）
- `restoreAllOSData()`：バックアップに `learningRadar_v1` があれば、そのまま JSON.stringify して書き戻す。中身の加工はしない（events・themes・settings が1オブジェクトに入っている）
- 復元ガードがキーごとに鮮度比較をしているなら、`updatedAt`（ISO）を比較キーに使う。無い場合はほかの OS と同じ扱い
- Task OS 側の表示（バックアップ対象一覧・件数表示など）があれば「学びレーダー」を追加。件数は `events.length`
- Task OS のそれ以外のロジックには触らない。Phase 1 の学びレーダー側にも変更不要

確認：

1. 学びレーダーにデータがある状態で Task OS からバックアップを実行し、出力 JSON に `learningRadar_v1` が入り、`events` の件数が OS 側と一致する
2. 学びレーダーの localStorage を消してから Task OS で復元し、学びレーダーを開くと元どおり表示される（id・status・statusHistory が保たれている）
3. `learningRadar_v1` が無い古いバックアップを復元してもエラーにならない

## 2. コックピット：カード追加

- 既存カードと同じ型で「学びレーダー」カードを追加。リンク先 `learning-radar/`（相対パス。他カードの書き方に合わせる）
- 説明は1行「セミナー・講座の締切を見逃さない」程度
- サブ情報は置かない（件数バッジ・新着数などは出さない。学びレーダーは静かな UI の方針）
- 並び順は既存の並びの規則に従う。規則が無ければ Project OS の隣

確認：コックピットからタップで学びレーダーが開く。他カードのレイアウトが崩れていない（375px / PC 幅）

## 3. 禁止事項

- task-os とコックピット以外の index.html に触らない
- 学びレーダーのデータ形式を変えない

## 4. 完了報告

- コミットハッシュ
- 確認1〜3の結果
- バックアップ JSON 内での `learningRadar_v1` の位置（他キーと同階層か）。Cowork の収集タスクがこれを読むので、パスを正確に

完了したら本依頼書を docs/specs/ へ移動してコミット。
