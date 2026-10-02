# 学びレーダー OS 依頼書（Phase 1）

- 作成日：2026-10-01  
- 宛先：Claude Code  
- 正本の要件定義：Claude Docs「学びレーダー 要件定義・概要設計」（本依頼書はその Phase 1 を実装可能な粒度に落としたもの）  
- 配置先：`learning-radar/index.html`（新規。my-apps リポジトリ直下に新フォルダ）  
- 初期データ：`learning-radar/seed/learning-events-seed.json`（同梱。Phase 0 で手動収集した 67 件）

## 0\. 作業前

1. `git pull` し、HEAD が origin/main と一致することを確認する  
2. 既存 OS の index.html は一切編集しない（my-apps 共通ルール）。Task OS への登録は Phase 2 の別依頼書で行う  
3. 参考実装：Project OS v2.1（カード展開・モーダル不使用）、1day OS（Drive から JSON を取り込む gdrive 系関数）

## 1\. 目的（1行）

学びテーマのセミナー・研修・展示会・講座を週1回のレビューで「申込か見送りか」決め切り、「後から見たらもう終わっていた」を無くす。

## 2\. スコープ（Phase 1 で作るもの・作らないもの）

作る：

- 単一 HTML の学びレーダー OS（localStorage キー `learningRadar_v1`）  
- ホーム＝週次レビュー画面（締切接近 → 新着 → 検討中 → 申込済み の縦1画面）  
- イベントのステータス遷移（ボタン一つ）と履歴  
- 新着 JSON の取込（Drive の `10_日次データ/learning-events.json` を createdTime 最新で取得。失敗時はファイル選択／貼り付けで代替）  
- 手動登録フォーム  
- テーマ設定画面（追加・停止・キーワード・除外語・定点観測先）  
- 設定（レビュー曜日・締切強調日数・新着強調日数）  
- 共有用コピー（カード全文・秘書向けテキスト）  
- PWA（manifest / service worker。他 OS と同じ型）  
- シード JSON の取込で初期データを入れられること

作らない（Phase 2・3 または対象外）：

- Task OS の collectAllOSData()/restoreAllOSData() への追加、コックピットのカード（Phase 2）  
- Cowork 側の週次収集タスク、Morning Brief への1行通知（Phase 2・3、Cowork 担当）  
- 取込の自動化（Phase 3）  
- Google カレンダー登録（対象外。本人が手動で入れる）  
- 秘書との共有画面（対象外）  
- 月次レビューへの集計・テーマ別参加実績（対象外。集計機能そのものを作らない）  
- Reflect OS 取込形式のコピー（F10・COULD。Phase 1 では見送り）

## 3\. 設計原則（竹嶋OS設計憲章 v2.0 準拠）

- ゼロ依存・ローカルファースト。単一 HTML、外部ライブラリなし、日本語 UI  
- 静かな UI。強調するのは「締切接近」だけ。バッジ・催促・件数カードは置かない  
- ステータス変更は `statusHistory` に積む。例外は「見過ごし」の消込で、これは events\[\] から物理削除する（本人判断：キャッチアップが目的なので見過ごしは残さない）。見送り・参加・終了は削除しない  
- モーダル不使用。カードはタップでその場展開（Project OS v2.1 の型）  
- スマホ対応。週次レビューを移動中に片手でできる幅（max-width 720px 程度・ボタンは指で押せる大きさ）  
- 空の節は非表示。「0件」を表示しない

## 4\. データ設計

### 4.1 localStorage `learningRadar_v1`

```json
{
  "version": 1,
  "events": [],
  "themes": [],
  "settings": {
    "reviewWeekday": 1,
    "deadlineSoonDays": 7,
    "newHighlightDays": 7,
    "ignoreTitleWords": [],
    "dismissed": [],
    "lastImportGeneratedAt": null,
    "lastImportAt": null
  },
  "updatedAt": "ISO"
}
```

- `reviewWeekday`：0=日 … 6=土。既定 1（月曜）  
- `dismissed`：見過ごしを消込した `{url, startDate, at}` の配列。重複判定（4.5）で既存と同じ扱い  
- `ignoreTitleWords`：タイトルにこの語を含むイベントは取込時に捨てる（全テーマ共通）。テーマ側の `excludeWords` も取込時に同じ判定に使う（4.5 参照）  
- 保存は1オブジェクトを丸ごと `JSON.stringify`。保存関数は `saveData()` に統一（gdrive 系の注意事項に合わせる）

### 4.2 events\[\] の1件

| 項目 | 型 | 内容 |
| :---- | :---- | :---- |
| id | string | OS 内で生成。`lr_` \+ Date.now().toString(36) \+ 乱数4桁 |
| title | string | イベント名 |
| organizer | string | 主催 |
| themeIds | string\[\] | 紐づくテーマ id（複数可。空配列可） |
| kind | enum | `seminar` / `training` / `course` / `expo` / `conference` / `study` / `community` |
| format | enum | `onsite` / `online` / `hybrid` / `archive` |
| location | string | 会場（onsite / hybrid のとき） |
| startDate | YYYY-MM-DD | 開催初日 |
| endDate | YYYY-MM-DD / null | 最終日。単発は null |
| time | string | 時間帯の表示文字列（"19:00〜21:00" など）。任意 |
| applyDeadline | YYYY-MM-DD / null | 申込締切。null は「要確認」表示 |
| fee | string | 費用の表示文字列（"無料" "66,000円"）。空可 |
| url | string | 公式ページ。重複判定の第一キー |
| summary | string | 1〜3行の要約・備考 |
| weekday | boolean | 平日開催か。取込時・保存時に startDate から再計算（土日＝false） |
| confidence | enum | `high` / `low`。日付・締切を公式ページで確認済みか |
| source | enum | `auto`（Cowork）/ `manual`（手入力）/ `seed`（初期データ） |
| foundAt | ISO | 発見日時 |
| status | enum | `new` / `considering` / `applied` / `attended` / `passed` / `missed` / `expired` |
| statusHistory | {status, at, note}\[\] | 遷移の履歴。生成時に `{status:'new', at}` を1件積む |
| note | string | 自由メモ |
| needsCheck | boolean | 自動取得できず締切・費用が空のもの。カードに「要手動確認」を出す |

kind / format の表示名：

- kind：セミナー / 研修 / 講座 / 展示会 / 学会 / 勉強会 / コミュニティ  
- format：対面 / オンライン / ハイブリッド / アーカイブ

### 4.3 themes\[\] の1件

| 項目 | 内容 |
| :---- | :---- |
| id | 短い識別子（`crisis` / `physical-ai` / `pmi` / `sensemaking` / `succession` / `project-design` / `converge`） |
| name | 表示名 |
| keywords | 検索語の配列 |
| excludeWords | 除外語の配列 |
| watchSources | 定点観測先 `{name, url, memo}[]`。memo に「毎年3月」「募集は5月・7月」などの周期を書く |
| active | 収集対象か |
| axisType | `fixed`（時期が決まっている）/ `play`（遊びの感覚）/ `new`（新規） |
| reviewAt | 次の見直し日（既定 2026-12-01） |

注意：学びの軸の正本は Morning Brief 側のまま。OS のテーマは収集用の設定として独立しており、Brief のローテに影響しない。`briefRotation` のようなフラグは持たない。

### 4.4 初期テーマ（初回起動時に themes が空なら投入する）

| id | name | axisType | keywords | excludeWords |
| :---- | :---- | :---- | :---- | :---- |
| crisis | 危機管理 | new | 危機管理 セミナー / クライシスマネジメント 研修 / BCP 講座 / 危機管理産業展 | — |
| physical-ai | フィジカルAI | new | フィジカルAI セミナー / フィジカルAI 展示会 / ヒューマノイド / ロボット工学セミナー | — |
| pmi | PMI | new | PMI M\&A セミナー / ポストマージャーインテグレーション 研修 / M\&A 統合 講座 | PMI日本支部 / PMP / PMBOK / プロジェクトマネジメント協会 |
| sensemaking | センスメイキング理論 | new | センスメイキング / 組織論 公開講座 / 組織学会 / 組織行動論 | — |
| succession | 承継 | fixed | 事業承継 セミナー / ファミリービジネス 講座 / 後継者 塾 | 税制 / 自社株評価 / M\&A仲介 / 求人 |
| project-design | PJ設計 | play | PMAJ セミナー / Backlog World / プロジェクト立ち上げ ワークショップ / P2M | PMP / 動画講座 |
| converge | フィジカル×サイバー融合 | fixed | Security Days / 危機管理産業展 サイバー / 重要インフラ 物理 サイバー / OTセキュリティ | 製品紹介 |

watchSources の初期値は末尾「付録A」の通り。

### 4.5 重複判定（取込時・手動登録時）

1. 第一キー：URL 正規化一致 ＋ startDate 一致。正規化＝小文字化・`http(s)://` と `www.` 除去・クエリ文字列と `#` 以降除去・末尾 `/` 除去  
2. 第二キー：タイトル正規化（全角半角統一・空白と記号を除去）＋ startDate 一致  
3. 一致したら取り込まない（既存を更新もしない）。件数を「重複 N 件」として取込結果に表示する。照合先は events\[\] と `settings.dismissed[]`（消込済みの見過ごし）の両方  
4. タイトル除外：`settings.ignoreTitleWords` と、そのイベントの themeIds に対応するテーマの `excludeWords` のいずれかをタイトルが含むなら取り込まない。件数を「除外 N 件」として表示する。手動登録には適用しない  
5. URL が同じでも startDate が違えば別レコード（同じページに毎月回・連続講座の説明会と本講座が載る例が Phase 0 で複数あった）。年次イベントも年が違えば別レコード

### 4.6 Cowork が書く JSON（取込の入力形式）

```json
{
  "generatedAt": "2026-10-04T21:00:00+09:00",
  "weekOf": "2026-10-05",
  "themesSearched": ["crisis", "physical-ai"],
  "newEvents": [ { "title": "...", "organizer": "...", "themeIds": ["crisis"], "kind": "seminar", "format": "onsite", "location": "...", "startDate": "2026-10-15", "endDate": null, "time": "9:45〜17:30", "applyDeadline": "2026-10-09", "fee": "66,000円", "url": "https://...", "summary": "...", "weekday": true, "confidence": "high", "source": "auto", "foundAt": "..." } ],
  "skippedAsDuplicate": 0
}
```

- `newEvents` の各要素は 4.2 のうち id / status / statusHistory / needsCheck を除いたもの  
- OS が取込時に id を振り、status を `new`、statusHistory に1件積む。applyDeadline と fee が両方空なら `needsCheck: true`  
- `generatedAt` が `settings.lastImportGeneratedAt` と同じなら「取込済みです」と出して何もしない  
- シード JSON（`seed/learning-events-seed.json`）も同じ形式。`source` は `seed`

## 5\. ステータス

| status | 表示 | 遷移元 | 遷移先（ボタン） | 備考 |
| :---- | :---- | :---- | :---- | :---- |
| new | 新着 | 取込・手動登録 | 検討 / 見送り |  |
| considering | 検討 | new | 申込 / 見送り | 公式ページで確認したら「確認済み」ボタンで confidence を high に |
| applied | 申込済み | considering / new | 参加 / 見送り | new から直接「申込」も可（締切が目前のとき） |
| attended | 参加 | applied | — | note に一言を残せる |
| passed | 見送り | new / considering / applied | 検討に戻す |  |
| missed | 見過ごし | 自動 | 消込（events\[\] から削除） | 消込済みの URL＋開催日は `settings.dismissed[]` に `{url, startDate}` で残し、再取込を防ぐ |
| expired | 終了 | 自動 | — | 「過去・見送り」に残る |

自動遷移（起動時と取込後に1回走らせる `autoTransition()`）：

- `new` / `considering` で applyDeadline が今日より前 → `missed`。applyDeadline が null のときは startDate が今日より前 → `missed`  
- `applied` で endDate（なければ startDate）が今日より前 → そのまま（参加したかは本人が押す。自動で attended にしない）  
- `passed` で endDate（なければ startDate）が今日より前 → `expired`  
- 自動遷移も statusHistory に `{status, at, note:'auto'}` を積む

「見送り」は失敗ではなく、「見過ごし」が本システムの失敗指標。この2つは必ず分ける。ただし件数の集計表示はしない。

## 6\. 画面

### 6.1 ホーム（週次レビュー）

上から順に節を縦に並べた1画面。該当が無い節は見出しごと非表示。

1. 見過ごし（`missed`）：薄い赤系の帯。カードに「消込」ボタンのみ。消込で events\[\] から削除され、`settings.dismissed[]` に URL＋開催日だけ残る（確認ダイアログは出さない。押し間違いは直後の「元に戻す」1行で5秒だけ救済）  
2. 締切接近：`new` / `considering` で applyDeadline が `deadlineSoonDays` 以内（null は含めない）。唯一の強調表示（左ボーダー＋締切までの日数「あと3日」）。ボタン：申込 / 見送り  
3. 新着：`new`（締切接近に出たものは除く）。テーマ別にグループ化。各グループ内は平日開催が上、土日開催は下に薄く（opacity 0.6 程度）。ボタン：検討 / 見送り / 申込  
4. 検討中：`considering`（締切接近を除く）。applyDeadline 昇順（null は最後に「要確認」）。ボタン：申込 / 見送り / 確認済み  
5. 申込済み：`applied`。startDate 昇順。ボタン：参加 / 見送り  
6. 折りたたみ「過去・見送り」：`attended` / `passed` / `expired`。既定で閉じる。F9 の「この団体は毎年この時期」を振り返る用途なので、organizer と startDate を見やすく

カード（閉じた状態・1行〜2行）：

- 1行目：タイトル（リンクではなくテキスト。URL はカード展開内）  
- 2行目：テーマ名 ・ 種別 ・ 形式 ・ 開催日（期間なら「10/27〜2/16」）・ 締切（「締切 10/16」／null は「締切 要確認」）・ 費用  
- confidence が low なら日付の後ろに「?」を添える。needsCheck なら「要手動確認」の小さなラベル  
- 土日開催は「土」「日」の小ラベル

カード（タップで展開）：

- 主催・会場・時間帯・要約・URL（別タブで開く a タグ）・note（インライン編集・blur で保存）  
- 「📋 コピー」：タイトル／主催／開催日時／会場／形式／費用／締切／URL をプレーンテキストで（F12 の秘書向け）  
- statusHistory を小さく時系列表示  
- ステータスボタン（6.1 の各節と同じもの）

ヘッダー：

- 左：タイトル「学びレーダー」  
- 右：「⬇ 取込」「＋ 登録」「⚙ テーマ・設定」の3つだけ  
- 最終取込日時を右上に小さく（例「取込 10/05 07:12」）。件数バッジは置かない

### 6.2 取込

「⬇ 取込」を押すと：

1. Drive 取得を試みる（6.4）。成功したら 4.5・4.6 の手順で取り込み、結果を1行表示「新着 12 件 / 重複 3 件 / 要手動確認 2 件」  
2. 失敗（未認可・ネットワーク）時は同じ画面に「ファイルを選ぶ」と「JSON を貼り付け」を出す。どちらも同じ取込関数に流す  
3. 取込後 `autoTransition()` を走らせ、ホームを再描画する

### 6.3 手動登録

「＋ 登録」で画面上部にインラインのフォームを展開（モーダル不使用）。項目：タイトル（必須）・主催・テーマ（複数チェック）・種別・形式・会場・開催日（必須）・最終日・時間帯・申込締切・費用・URL・メモ。保存で `source: manual`、`confidence: high`、`status: new`。重複判定は 4.5 と同じ（重複なら保存せず「同じ URL が登録済み」と出す）。

### 6.4 Drive 取得（1day OS の gdrive 系をコピーして定数を差し替える）

- 親フォルダ：`10_日次データ`（ID `1qOQXKraLlYA8BA3WM1dvNdVGzHasRWKP`）  
- ファイル名：`learning-events.json`（定数 `GDRIVE_FILE_NAME`。gdriveFindFile の URL はこの定数を参照する。ハードコードしない）  
- 検索：親フォルダ ID ＋ ファイル名で `createdTime desc` の先頭を採用（Cowork の Drive コネクタは同名新規作成しかできないため）  
- `includeItemsFromAllDrives=true` / `supportsAllDrives=true` を維持  
- トークンキー：`gdrive_token_learningradar`（他 OS と衝突させない）  
- CLIENT\_ID・リダイレクト URI は既存 OS と同じものを使う。リダイレクト URI に `learning-radar/` の登録が必要なら、作業完了報告に「要登録」と書く  
- gdriveLoad 後の保存は `saveData()` を呼ぶ

### 6.5 テーマ・設定

1画面にテーマ一覧（上）と設定（下）。

テーマ一覧：

- 各テーマがカード。閉じた状態＝名前・active トグル・axisType ラベル・「この3か月：拾った N 件 / 検討に進んだ M 件」（事実表示のみ。色・警告なし）  
- 展開＝name / keywords（1行1語のテキストエリア）/ excludeWords（同）/ watchSources（name・url・memo の行を追加・削除）/ axisType / reviewAt。blur で保存  
- 「＋ テーマを追加」。id は name から自動生成（英数字に変換できない場合は `theme_` \+ 時刻）  
- 削除ボタンは置かない。停止は active=false

設定：

- レビュー曜日（セレクト）  
- 締切強調日数（既定 7）  
- 新着強調日数（既定 7。ホームの「新着」節に残す期間ではなく、カードの「NEW」小ラベルを付ける期間）  
- 取込時に無視するタイトル語（1行1語のテキストエリア。`settings.ignoreTitleWords`）  
- 「全データをエクスポート」（JSON ダウンロード）/「インポート」（JSON を丸ごと置換。確認1回）

### 6.6 見た目

- 既存 OS と同じ系統（白地・グレー基調・角丸カード・システムフォント）。色はステータスを示す最小限（締切接近の左ボーダーのみアクセント色、見過ごしは薄い赤帯）  
- 文字は本文 15〜16px。スマホで指で押せるボタン高さ（36px 以上）  
- 絵文字はヘッダーのボタンと「📋 コピー」程度に留める

## 7\. 共有用コピーの書式（F12）

```
【学びレーダー】
タイトル：
主催：
日時：2026-10-15（木）9:45〜17:30
会場：六本木（対面）
費用：66,000円
申込締切：2026-10-09
URL：
```

曜日は startDate から付ける。期間のときは「2026-10-27（火）〜2027-02-16（火）毎週火曜」のように endDate も出す（曜日は startDate のみ）。

## 8\. PWA

- `learning-radar/manifest.json`・`learning-radar/sw.js` を他 OS と同じ型で作る。name「学びレーダー」、short\_name「学びレーダー」、theme\_color は既存 OS に合わせる  
- service worker は index.html と manifest のみキャッシュ。更新時に古いキャッシュを消す（他 OS で問題になった古いキャッシュ残りの対策を踏襲）

## 9\. 受入条件

1. 初回起動で 7 テーマが投入され、ホームは空（何も強調されていない）  
2. `seed/learning-events-seed.json` をファイル選択で取り込むと 67 件が入り、ホームに「締切接近」「新着」が並ぶ。同じファイルをもう一度取り込むと「取込済みです」で件数が増えない  
3. 新着カードの「検討」を押すと検討中の節へ移り、statusHistory に2件（new → considering）が残る  
4. applyDeadline を今日より前に手で編集した `new` のイベントは、リロード後に「見過ごし」節へ移る。「消込」を押すと events\[\] から消え、同じ URL＋開催日を含む JSON を再取込しても戻らない  
5. 手動登録で既存と同じ URL を入れると保存されず、その旨が表示される  
6. テーマを停止（active=false）しても既存イベントは消えない。テーマカードの「この3か月」の件数が実データと一致する  
7. スマホ幅（375px）でホームの全ボタンが押せ、横スクロールが出ない  
8. Drive 未認可の状態で「⬇ 取込」を押すと、エラーで止まらずファイル選択／貼り付けに切り替わる  
9. 件数バッジ・催促文言・「0件」表示がどこにも無い  
10. 他 OS の index.html に差分が無い（git diff で確認）

## 10\. 完了報告に含めること

- コミットハッシュ  
- リダイレクト URI の登録が必要かどうか  
- Phase 2 で Task OS 側に追加するキー名（`learningRadar_v1`）と、collectAllOSData() に入れる際の注意（統合バックアップは 1 オブジェクトをそのまま格納）

---

## 付録A　watchSources の初期値（Phase 0 で確認した定点観測先）

| theme | name | url | memo |
| :---- | :---- | :---- | :---- |
| crisis | リスク対策アカデミー | [https\://academy.risktaisaku.com/event/](https://academy.risktaisaku.com/event/) | 毎月。対面講座は六本木 |
| crisis | 危機管理カンファレンス | [https\://risk-conference.net/](https://risk-conference.net/) | 春・秋の年2回、無料オンライン |
| crisis | SOMPOリスクマネジメント セミナー | [https\://www\.sompo-rc.co.jp/seminars](https://www.sompo-rc.co.jp/seminars) | 無料〜有料 |
| crisis | JSSC 行事予定 | [https\://jssc.gr.jp/yotei/](https://jssc.gr.jp/yotei/) | 詳細はPDF・メール問い合わせ |
| crisis | 日本危機管理防災学会 | [https\://www\.jemaweb.org/](https://www.jemaweb.org/) | 研究大会11月 |
| crisis | 危機管理産業展 RISCON | [https\://www\.kikikanri.biz/](https://www.kikikanri.biz/) | 毎年9〜10月 ビッグサイト |
| physical-ai | ロボスタ | [https\://robotstart.info/](https://robotstart.info/) | 無料オンラインセミナーシリーズ |
| physical-ai | 日本ロボット学会 セミナー | [https\://www\.rsj.or.jp/event/seminar/news/](https://www.rsj.or.jp/event/seminar/news/) | 毎月オンライン・見逃し配信あり |
| physical-ai | NexTech Week | [https\://www\.nextech-week.jp/](https://www.nextech-week.jp/) | 秋11月幕張・春4月ビッグサイト |
| physical-ai | アールティ セミナー | [https\://rt-net.jp/](https://rt-net.jp/) | Isaacハンズオン |
| pmi | 日本M\&Aセンター セミナー | [https\://www\.nihon-ma.co.jp/seminar/list.php?year=2026](https://www.nihon-ma.co.jp/seminar/list.php?year=2026) | PMI 1日研修会 毎月 |
| pmi | 東京都中小企業振興公社 PMI | [https\://www\.tokyo-kosha.or.jp/support/revival/seminar.html\#PMI](https://www.tokyo-kosha.or.jp/support/revival/seminar.html#PMI) | スクール年2期（募集5月・7月）・セミナー年2回 |
| pmi | 日経イベント PMI | [https\://events.nikkei.co.jp/tag/pmi/](https://events.nikkei.co.jp/tag/pmi/) | 1月・9月に大型 |
| sensemaking | ビジネスリサーチラボ Peatix | [https\://peatix.com/group/9909/events](https://peatix.com/group/9909/events) | センスメイキング名義のほぼ唯一の定期発信源 |
| sensemaking | 組織学会 | [https\://www\.aaos.or.jp/conference](https://www.aaos.or.jp/conference) | 年次大会10月・研究発表大会6月。自動取得不可 |
| sensemaking | 日経BS MBA Essentials | [https\://school.nikkei.co.jp/seminar/list?tag=122](https://school.nikkei.co.jp/seminar/list?tag=122) | 早稲田WBS教員の組織論講座 |
| succession | 東商イベント検索 | [https\://myevent.tokyo-cci.or.jp/tile.php?searching\_name=事業承継](https://myevent.tokyo-cci.or.jp/tile.php?searching_name=事業承継) | 支部単位で毎月 |
| succession | 事業承継センター | [https\://www\.jigyousyoukei.co.jp/seminar/future/](https://www.jigyousyoukei.co.jp/seminar/future/) | しながわ後継者塾・後継者塾ベーシック。年度初め募集 |
| succession | FBAA | [https\://fbaa.jp/archives/seminar](https://fbaa.jp/archives/seminar) | 定例は平日夜Zoom。基礎プログラムは9月中旬締切 |
| succession | 中小企業大学校 東京校 | [https\://www\.smrj.go.jp/](https://www.smrj.go.jp/) | 事業承継セミナー 年数回 |
| project-design | PMAJ イベントカレンダー | [https\://www\.pmaj.or.jp/kyoukai/event\_calendar.html](https://www.pmaj.or.jp/kyoukai/event_calendar.html) | 平日夜の月例・特別講座 |
| project-design | JBUG Doorkeeper | [https\://backlogworld.doorkeeper.jp/](https://backlogworld.doorkeeper.jp/) | 年1回の大会＋随時WS |
| project-design | コパイロツト | [https\://www\.copilot.jp/seminar/](https://www.copilot.jp/seminar/) | プロジェクトBoost\!。次回未告知 |
| project-design | PMI日本支部 | [https\://www\.pmi-japan.org/event-seminar/](https://www.pmi-japan.org/event-seminar/) | 詳細は要ログイン・手動確認 |
| converge | Security Days | [https\://f2ff.jp/](https://f2ff.jp/) | 3月・10月 |
| converge | SECURITY SHOW | [https\://messe.nikkei.co.jp/ss/](https://messe.nikkei.co.jp/ss/) | 毎年3月 ビッグサイト |
| converge | 慶應 サイバーセキュリティ国際シンポ | [https\://symp.cysec-lab.keio.ac.jp/](https://symp.cysec-lab.keio.ac.jp/) | 毎年10月末 |
| converge | 全国警備業協会 お知らせ | [https\://www\.ajssa.or.jp/news/](https://www.ajssa.or.jp/news/) | 会員向け。JSS社内の案内を転送してもらう運用 |
| converge | JNSA セミナー | [https\://www\.jnsa.org/seminar/](https://www.jnsa.org/seminar/) |  |

## 付録B　Phase 2・3 の見通し（本依頼書の対象外・参考）

- Phase 2（Claude Code）：Task OS の collectAllOSData()/restoreAllOSData() に `learningRadar_v1` を追加、コックピットにカード追加  
- Phase 2（Cowork）：週次収集タスクの恒久ルールパッチ。手順は要件定義ドキュメントの「収集設計」節。Phase 0 で分かった点＝テーマ名検索で当たるのは危機管理とフィジカルAIだけなので、watchSources を直接開く手順を必須にする  
- Phase 3：取込の自動化、レビュー日の Brief に1行通知（任意）