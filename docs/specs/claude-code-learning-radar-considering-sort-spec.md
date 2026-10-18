# 依頼書：学びレーダー「検討中」を開催日順に並べる（2026-10-18）

依頼者：竹嶋（Cowork参謀が起票）／対象：`learning-radar/index.html`／規模：1行

## 背景
竹嶋さん（10/18）：「学びレーダーの検討中のブロックは日付順の並び替えにしてほしい」
いまの「検討中」は申込締切が先、開催日が後の順で並んでいる。締切が「要確認」のものは末尾に回るため、10/22開催のセミナーが11/19・11/27開催より下に出ている。

## 現状（renderHome 内）
```js
const cons = ev.filter(e => e.status === 'considering' && !isSoon(e)).sort(by(e => (e.applyDeadline || '9999-99-99') + e.startDate));
```

## 変更
並びのキーを開催日（startDate）だけにする。申込済みと同じ並び方になる。開催日が空のものは末尾に回す。
```js
const cons = ev.filter(e => e.status === 'considering' && !isSoon(e)).sort(by(e => (e.startDate || '9999-99-99') + (e.applyDeadline || '9999-99-99')));
```
開催日が同じものは、締切が早いほうを上にする。

## 変えないもの
- 絞り込み（`status === 'considering'`）と、締切が近いものを「締切接近」の節に分ける処理（`!isSoon(e)`）はそのまま残す
- 新着・申込済み・締切接近の並び
- データ（learningRadar_v1）には触れない

## 確認
- いまのデータで、検討中が 10/22 → 11/19 → 11/27 の順に並ぶこと
- 開催日が空のカードがあれば、いちばん下に出ること
