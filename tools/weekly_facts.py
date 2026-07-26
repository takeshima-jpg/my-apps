#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly_facts.py — 週次レビュー用「事実」計算スクリプト
=====================================================
目的：Coworkに推測させず、completedAt / 実行日ベースで「今週の完了・実行」を機械的に確定する。
     「データから消えただけ」「却下(rejected)」「破棄(discarded)」は完了に混ぜない。

使い方：
    python3 weekly_facts.py myapps-all-backup-YYYY-MM-DD.json
        → 対象週 = 直近の月曜〜日曜（今日を含む週）
    python3 weekly_facts.py backup.json 2026-07-06
        → 指定日を含む週（月曜起点）を対象にする
    python3 weekly_facts.py backup.json 2026-07-06 --prev
        → 前週も併せて出す（週次v3の「前週との再掲禁止」判定用）

出力：weekly-facts.json（同ディレクトリ）＋ 標準出力にサマリ。
      このJSONをCoworkに渡し、Coworkは「数える」のをやめて「意味を読む」ことに専念する。
"""
import json, sys, os
from datetime import datetime, date, timedelta
from collections import Counter

# ---------- 日付ユーティリティ ----------
def parse_dt(s):
    """ISO文字列/日付文字列を date に。失敗は None。"""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    # 'YYYY-MM-DD...' の先頭10文字を優先的に採用
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        pass
    for fmt in ("%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except Exception:
            continue
    return None

def week_bounds(anchor: date):
    """anchorを含む週の月曜(start)〜日曜(end)を返す。"""
    start = anchor - timedelta(days=anchor.weekday())  # 月曜
    end = start + timedelta(days=6)                     # 日曜
    return start, end

def in_week(d, start, end):
    return d is not None and start <= d <= end

# ---------- 各OSの「今週の完了/実行」抽出 ----------
def facts_for_week(d, start, end):
    out = {}

    # Shot Task OS：完了 = status=='done' かつ completedAt が今週内
    #   ※ rejected(却下) は完了ではない。status を必ず併用する。
    shot_done = []
    for t in d.get('shotTaskOS', []):
        if t.get('status') == 'done':
            cd = parse_dt(t.get('completedAt'))
            if in_week(cd, start, end):
                shot_done.append({"title": t.get('title'), "date": cd.isoformat()})
    out['shot_completed'] = shot_done

    # 100LIST：完了 = completed==True かつ completedAt が今週内、かつ discarded でない
    list_done = []
    for it in d.get('list100', []):
        if it.get('completed') and not it.get('discarded'):
            cd = parse_dt(it.get('completedAt'))
            if in_week(cd, start, end):
                list_done.append({"title": it.get('title'), "date": cd.isoformat()})
    out['list100_completed'] = list_done

    # Routine OS：実行 = logs の actionDate が今週内（1ログ=1実行イベント）
    routine_done = []
    for lg in d.get('routineOS', {}).get('logs', []):
        ad = parse_dt(lg.get('actionDate'))
        if in_week(ad, start, end):
            routine_done.append({
                "title": lg.get('title'),
                "date": ad.isoformat(),
                "action": lg.get('action'),
                "skipReason": lg.get('skipReason') or None,
            })
    out['routine_actions'] = routine_done

    # Lectica：実験実行 = lecticaLogs の date が今週内
    lectica_done = []
    exp_title = {}  # L0xx -> タイトル
    for e in d.get('lecticaExperiments', []):
        eid = e.get('id') or e.get('experimentId')
        if eid:
            exp_title[eid] = e.get('title') or e.get('name')
    for lg in d.get('lecticaLogs', []):
        dt = parse_dt(lg.get('date') or lg.get('createdAt'))
        if in_week(dt, start, end):
            eid = lg.get('experimentId')
            lectica_done.append({
                "experimentId": eid,
                "title": exp_title.get(eid),
                "date": dt.isoformat(),
            })
    out['lectica_logs'] = lectica_done

    # 1day OS：記録 = onedayLogs の date が今週内（活動量・満足度の材料）
    oneday = []
    for lg in d.get('onedayLogs', []):
        if lg.get('archived'):
            continue
        dt = parse_dt(lg.get('date'))
        if in_week(dt, start, end):
            oneday.append({
                "date": dt.isoformat(),
                "satisfaction": lg.get('satisfaction'),
                "flags": lg.get('flags') or [],
                "tags": lg.get('tags') or [],
                "has_unease": bool((lg.get('unease') or '').strip()),
            })
    out['oneday_logs'] = oneday

    # Project OS：今週「更新のあった」プロジェクト（updatedAtが今週内）。状態値も添える。
    #   完了ではなく「動きのあったProject」。状態遷移の解釈はCowork側。
    proj = []
    for p in d.get('projectOS', {}).get('projects', []):
        ud = parse_dt(p.get('updatedAt'))
        if in_week(ud, start, end):
            proj.append({"name": p.get('name'), "status": p.get('status'), "updated": ud.isoformat()})
    out['project_updated'] = proj

    return out

def summarize(facts):
    """人が一目で読めるカウントサマリ。"""
    s = {
        "shot_completed": len(facts['shot_completed']),
        "list100_completed": len(facts['list100_completed']),
        "routine_actions": len(facts['routine_actions']),
        "lectica_logs": len(facts['lectica_logs']),
        "oneday_logs": len(facts['oneday_logs']),
        "project_updated": len(facts['project_updated']),
    }
    # 1dayの満足度分布・フラグ分布
    if facts['oneday_logs']:
        s['oneday_satisfaction'] = dict(Counter(x['satisfaction'] for x in facts['oneday_logs']))
        flags = Counter()
        for x in facts['oneday_logs']:
            for f in x['flags']:
                flags[f] += 1
        s['oneday_flags'] = dict(flags)
    return s

# ---------- メイン ----------
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = [a for a in sys.argv[1:] if a.startswith('--')]
    if not args:
        print("usage: python3 weekly_facts.py <backup.json> [anchor-YYYY-MM-DD] [--prev]")
        sys.exit(1)
    path = args[0]
    anchor = parse_dt(args[1]) if len(args) > 1 else date.today()
    want_prev = '--prev' in opts

    d = json.load(open(path, encoding='utf-8'))
    start, end = week_bounds(anchor)

    result = {
        "generated_at": datetime.now().isoformat(timespec='seconds'),
        "source_savedAt": d.get('savedAt'),
        "week": {"start": start.isoformat(), "end": end.isoformat()},
        "facts": facts_for_week(d, start, end),
    }
    result["summary"] = summarize(result["facts"])

    if want_prev:
        pstart, pend = week_bounds(start - timedelta(days=1))
        pf = facts_for_week(d, pstart, pend)
        result["prev_week"] = {
            "week": {"start": pstart.isoformat(), "end": pend.isoformat()},
            "summary": summarize(pf),
            "facts": pf,
        }

    outpath = os.path.join(os.path.dirname(os.path.abspath(path)), "weekly-facts.json")
    json.dump(result, open(outpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    # 標準出力サマリ
    print(f"対象週：{start} 〜 {end}（backup savedAt: {result['source_savedAt']}）")
    print("── 今週の確定実績（completedAt/実行日ベース）──")
    for k, v in result["summary"].items():
        print(f"  {k}: {v}")
    if want_prev:
        print("── 前週 ──")
        for k, v in result["prev_week"]["summary"].items():
            print(f"  {k}: {v}")
    print(f"\n→ {outpath} を出力。これをCoworkに渡してください。")

if __name__ == "__main__":
    main()
