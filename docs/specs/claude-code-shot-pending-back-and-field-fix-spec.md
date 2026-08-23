# Claude Code 実装依頼書：Shot OS 保留カードに「未着手に戻す」ボタン＋依頼書⑥の実装漏れ対応

作成日：2026-08-23
対象：`shot-task-os/index.html`、および（②で）`launcher/index.html`・`task-os/index.html`
作業前に必ず `git pull`（HEAD=5094d34以降であること）。

## 経緯
本件①は設計チャット側で実装・playwright検証まで完了していたが、その後に 194e881・5094d34 が
先にpushされたため、検証済みファイルの丸ごと差し替えは不可になった。**以下の差分を現行HEADに適用**すること。

## ① 保留カードに「未着手に戻す」ボタン（検証済みの差分を適用）

### 1. カードのアクションボタン分岐（renderTaskCard内・acts組み立て）
現行：`if (t.status !== 'done')` の枝で 今日/完了/保留 を一律に出している。
変更：保留中カードは「保留」の代わりに「未着手に戻す」を出す。

```js
    acts += `<button class="act-btn ab-tmr" onclick="setToday('${id}')">今日</button>`;
    acts += `<button class="act-btn ab-done" onclick="changeStatus('${id}','done')">完了</button>`;
    if (t.status === 'pending') {
      // 保留中カード：保留ボタンの代わりに未着手へ戻す導線を出す
      acts += `<button class="act-btn ab-back" onclick="changeStatus('${id}','todo')">未着手に戻す</button>`;
    } else {
      acts += `<button class="act-btn ab-pend" onclick="changeStatus('${id}','pending')">保留</button>`;
    }
```

※194e881で✔完了に確認ダイアログが入っている場合、完了ボタンの記述が上と異なる可能性がある。
その場合は**完了ボタンは現行のまま**とし、「保留⇔未着手に戻す」の入替部分だけを適用すること。

### 2. changeStatus に自動pauseフラグの掃除を追加
自動pause由来のLectica（`lecticaAutoPaused`・期日が過去）をそのままtodoに戻すと、
次回ロードの `lxAutoPause()` で**再び保留化されてしまう**。これを防ぐ。

```js
function changeStatus(id, status) {
  const t = tasks.find(x => x.id === id); if (!t) return;
  t.status = status;
  t.updatedAt = new Date().toISOString();
  if (status === 'done') t.completedAt = new Date().toISOString();
  else t.completedAt = null;
  // 未着手/進行中へ戻すときは自動pauseフラグを外す（期日が過去のままだと次回ロードで再pauseされるため）
  if ((status === 'todo' || status === 'doing') && t.lecticaAutoPaused) {
    delete t.lecticaAutoPaused;
    if (t.dueDate && t.dueDate < getTodayKey()) t.dueDate = getTodayKey();  // 期日も今日に引き上げて再pauseを防ぐ
  }
  save(); render();
}
```

※5094d34でchangeStatusに変更が入っている場合は、既存の処理を残した上で
「フラグ掃除＋期日引き上げ」の2行分だけを追加すること（丸ごと置き換えない）。

### 検証（設計チャット側でplaywright実施済み・同じ観点で再確認）
- 保留カード：「未着手に戻す」表示・「保留」非表示
- 未着手/進行中カード：従来どおり「保留」表示・「戻す」なし
- 完了カード：従来どおり「戻す」（既存挙動を変えない）
- 押すとtodoに遷移・リロード後維持
- lecticaAutoPaused付き（期日過去）を戻す → フラグ消滅・期日が今日・**リロードで再pauseされない**
- 構文検証（node --check）・コンソールエラーなし

## ② 依頼書⑥の実装漏れ対応【重要】

b8d00fa で改訂依頼書（`claude-code-lectica-random-removal-and-full-memo-spec.md` の
「⑥ aix_lectica_pending の読み取りを新旧フィールド名の両対応にする」）を格納済みだが、
**コードは未実装のまま**（origin/main確認：launcher 6箇所・task-os 2箇所が旧名 `selectedExperimentId` /
`selectedExperimentTitle` のみを読んでいる。launcher 364/367/644/657/672行、task-os 1708/1719行付近）。

Coworkは現在 `experimentId` / `title` 形式で出力しており（2026-08-21実測）、このままでは
- ランチャーのLecticaカードが「(実験名なし)」表示
- task-osが提案を「無し」と判定し、Lectica Shotが生成されない
が継続する。依頼書⑥のとおり、**全読み取り箇所**を
`pending.experimentId || pending.selectedExperimentId`／`pending.title || pending.selectedExperimentTitle`
の両対応に修正すること（launcherの lectica_daily_practice 判定 364行も同様）。

### 検証
- 新形式JSON（experimentId/title）→ カードにタイトル表示・Shot生成される
- 旧形式JSON（selectedExperimentId/selectedExperimentTitle）→ 同じ挙動（後方互換）

## コミット（2つに分けてよい）
1. 「shot-task-os: 保留カードに『未着手に戻す』ボタンを追加（保留ボタンと入替）。自動pause由来のLecticaを戻す際はlecticaAutoPausedを外し期日を今日へ引き上げ、次回ロードでの再pauseを防止」
2. 「task-os/launcher: aix_lectica_pendingの読み取りを新旧フィールド名両対応に（依頼書⑥の実装漏れ対応・(実験名なし)表示とShot未生成を解消）」

## 報告
①の適用結果（コンフリクトの有無）／②の修正箇所一覧／検証結果。実装を止める場合のみ質問を1つ。
