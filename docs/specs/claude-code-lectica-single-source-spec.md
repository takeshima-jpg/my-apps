# Claude Code 実装依頼書：Lectica出題をCowork提案優先にする（ランダムは厳密なフォールバックに降格）

作成日：2026-08-18
**改訂 v2（2026-08-18）：初版の「ランダム生成を廃止」は撤回する。ランダムは残すが、
提案が無い場合に限り、かつ同期完了後にのみ生成する。初版を受け取り済みの場合は本書で置き換えること。**

対象：`task-os/index.html` の `autoGenLecticaShot()` と起動時処理、`launcher/index.html` の `addLecticaShot()`
作業前に `git pull`。

## 竹嶋さんの求める運用（これが正）

- Brief（Cowork）の「今日の実験（Lectica×Reflect統合枠）」の実験が、**Shot OSのタスクに入り、Task OSに表示される**
- ランダム生成の「今日のLectica実験」は、**Brief提案が何も無かった時以外、どこにも表示されない**

## 問題（2026-08-18 実機で確認）

Brief本文は L042「育成対象を1人決めて観察してみる」。
しかしTask OSに出ていたのはランダム生成の別実験。原因は2つ重なっている。

### ① 同期前にランダムが先に座る
`task-os/index.html` 末尾（DOMContentLoaded）に次の分岐がある：

```js
if(gdToken){ setTimeout(()=>{ gdAutoSync(false); }, 1200); }
else { setTimeout(()=>{ if(autoGenLecticaShot()>0) renderHome(); }, 300); }
```

GDrive未ログインだと、**ページを開いて300ms後にランダム生成が走る**。
この時点で `aix_lectica_pending` はまだ無いので、必ずランダムが当日枠を埋める。

### ② 提案が届いても差し替わらない場合がある
同期時（C3）に再度 `autoGenLecticaShot()` が走り、ランダム由来かつ未完了なら提案で差し替える実装になっている。
それでも差し替わらないのは、当日分の `aix_lectica_pending` が存在しない時。
（Cowork側の `lectica_daily_practice` 出力要件は `docs/prompts/cowork-feedback-brief-slim-2026-08-18.md` 追補4で別途対応済み）

## 修正内容

### A. ランダム生成の条件を厳しくする

`autoGenLecticaShot()` に、**ランダム分岐を実行してよいかの引数**を追加する
（例：`autoGenLecticaShot(allowRandom)`。既定は `false`）。

- **提案（当日の有効な `aix_lectica_pending`）がある場合** → 従来どおり提案でShot生成。`allowRandom` は無関係
- **提案が無い場合**
  - `allowRandom === true` → ランダム生成する（従来のロジックのまま）
  - `allowRandom === false` → **何も生成せず return 0**

### B. 呼び出し側を3箇所そろえる

| 呼び出し箇所 | 行 | allowRandom |
|---|---|---|
| `handleAixTaskImport()`（AIタスク読込） | 998 付近 | **true** |
| `gdAutoSync()` C3（GDrive同期） | 2389 付近 | **true** |
| DOMContentLoaded の未ログイン分岐 | 2435 付近 | **false** |

**未ログインでTask OSを開いただけの日は、Lecticaを1件も出さない。**【竹嶋さん確認済み・厳守】
提案が届く前に埋めてしまうことが今回の不具合の原因であり、空のまま待つ方が正しい。
同期すればその場で提案が入る。

### C. 催促しない
Lectica Shotが無い日に「今日の実験がありません」等の警告・空カード・プレースホルダを**出さない**。
何も無い日は何も表示しない（設計憲章：signal over noise／催促しない）。

### D. 変更しないこと【厳守】
- 提案による差し替えロジック（random由来かつ未完了のときだけ差し替え・冪等）
- 手動追加・完了済み・sanbo由来のShotは上書きしない
- `lecticaSource`（'sanbo'／'random'）の意味と付与ルール
- 14日連続回避のロジック（ランダム分岐でのみ使う）

---

## 追補：`addLecticaShot()` の二重防止基準を揃える

対象：`launcher/index.html` の `addLecticaShot()`

### 問題
二重作成の防止基準が2箇所で食い違っている。

| 関数 | 場所 | 判定基準 |
|---|---|---|
| `autoGenLecticaShot()` | task-os | **カテゴリ**（当日のLecticaがあれば何もしない） |
| `addLecticaShot()` | launcher | **実験ID**（同じ実験IDが当日にあれば追加しない） |

そのためランダムのL035が入っている状態で今日タブの「今日のShotに追加」を押すと、
IDが異なるL042が**2件目として追加される**。

### 修正内容
`addLecticaShot()` の二重防止を**カテゴリ基準に揃える**。当日の `category==='Lectica'` のShotを探して：

1. **存在しない** → 従来どおり新規追加
2. **存在し、実験IDが同じ** → 何もしない（「今日のこの実験は追加済みです」）
3. **存在し、実験IDが違い、`status` が `'todo'` または `'doing'`**
   → **追加せず、そのShotを提案内容で置き換える**（title / category / memo / updatedAt を更新。idは変えない）。
   トーストは「今日のLecticaを提案内容に置き換えました」
4. **存在し、`status` が `'done'` / `'pending'` / `'rejected'`**
   → **何もしない**。実行済み・保留済みを上書きしない。トーストは「今日のLecticaは処理済みです」

原則：**提案（Cowork）が正、Task OS側は写し**。本体と同じ思想に揃える。

### 変更しないこと【厳守】
- Lecticaカテゴリ以外のShotには一切触れない
- `renderTodayLectica()` の「追加済み」表示判定は実験ID一致のままでよい
  （置き換え後はIDが一致するので結果は正しくなる）

---

## 検証
- 構文検証（node --check）
- **未ログインでTask OSを開く** → Lectica Shotが生成されない・コンソールエラーなし・HOMEに空要素が出ない
- 未ログインで開いた後にログイン同期 → 当日提案があればその実験でShotが1件生成される
- 同期時に提案あり → 提案の実験でShot生成（1件）
- 同期時に提案なし → ランダムで1件生成される
- ランダム生成済み＋後から提案着信（AIタスク読込） → 提案の内容に差し替わる・件数は1件のまま
- 差し替え後に再取り込みしても変化しない（冪等）
- 完了済み・手動追加のShotは差し替わらない
- 今日タブ「今日のShotに追加」：別IDの当日Lectica（todo）あり → 件数が増えず内容が置き換わる
- 今日タブ「今日のShotに追加」：当日Lecticaがdone → 何も起きない
- Lectica以外のカテゴリのShotが一切変化しない
- リロード後維持

## コミット
「task-os/launcher: Lectica出題をCowork提案優先に。ランダム生成はallowRandom引数で
同期・AIタスク読込時のみに限定し、未ログイン起動時は生成しない。あわせてaddLecticaShotの
二重防止をカテゴリ基準に揃え、別IDの当日Lecticaは追加ではなく置き換える（差し替えの冪等性は維持）」

## 報告
変更ファイル／`allowRandom` の実装方法と3箇所の呼び分け／未ログイン起動時の挙動／
addLecticaShotの置き換え実装／テスト結果。実装を止める場合のみ質問を1つ。
