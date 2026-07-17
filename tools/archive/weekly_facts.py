#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
週次「事実の差分」を機械計算する（推測禁止・すべてデータから算出）。

使い方:
    python tools/weekly_facts.py <今週のbackup.json> <先週のスナップショット.json>
    python tools/weekly_facts.py <今週> <先週> --out path/to/aix_weekly_facts.json

出力:
    aix_weekly_facts.json（Coworkの作業フォルダに置く用）＋ 標準出力にmarkdown表

期間の定義:
    「今週」= 先週スナップショットのsavedAt 〜 今週backupのsavedAt
    - 時刻付きの値（completedAt / createdAt）は (先週savedAt, 今週savedAt] の半開区間で判定する。
      先週スナップショット取得より前に完了したものを二重計上しないため。
    - 日付のみの値（lecticaLogs.date / onedayLogs.date / lastContactDate / changeLog.date）は
      [先週savedAtの日付, 今週savedAtの日付] の閉区間で判定する（時刻情報が無いため）。
    日付はいずれもローカルタイム（JST）に変換してから比較する。
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta

# 共通ヘルパは check_backup_health と共有する
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_backup_health as H  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass


# 未完了とみなすShotのstatus（done=完了 / rejected=却下 は未完了ではない）
SHOT_OPEN = ('todo', 'pending')
# 「重要」とみなすプロジェクトのpriority
IMPORTANT_PRIORITY = ('A', '高')
# プロジェクトの活動シグナルとして見る配列
PROJECT_ITEM_FIELDS = ('events', 'forks', 'decisions', 'learnings', 'issues', 'constraints')


# ── 日付ユーティリティ ─────────────────────────────────────────

def local_date(v):
    """ISO日時 or YYYY-MM-DD を、ローカルタイムの date にする。失敗時 None。"""
    dt = H.parse_iso(v)
    if dt is not None:
        return dt.astimezone().date()
    return H.parse_ymd(v)


def date_range(d_from, d_to):
    """d_from〜d_to（両端含む）の date を順に返す。"""
    days, cur = [], d_from
    while cur <= d_to:
        days.append(cur)
        cur += timedelta(days=1)
    return days


class Period:
    """今週の期間。時刻付きは半開区間、日付のみは閉区間で判定する。"""

    def __init__(self, prev_saved_at, cur_saved_at):
        self.start_dt = H.parse_iso(prev_saved_at)
        self.end_dt = H.parse_iso(cur_saved_at)
        if self.start_dt is None or self.end_dt is None:
            raise ValueError('savedAt を解釈できません（今週={!r} 先週={!r}）'.format(cur_saved_at, prev_saved_at))
        if self.end_dt < self.start_dt:
            raise ValueError('今週のsavedAtが先週より古いです。引数の順序を確認してください（今週 先週）。')
        self.start_date = self.start_dt.astimezone().date()
        self.end_date = self.end_dt.astimezone().date()

    def has_ts(self, v):
        """時刻付きの値が期間内か: (start, end]"""
        dt = H.parse_iso(v)
        return dt is not None and self.start_dt < dt <= self.end_dt

    def has_date(self, v):
        """日付のみの値が期間内か: [start_date, end_date]"""
        d = local_date(v)
        return d is not None and self.start_date <= d <= self.end_date

    def days(self):
        return date_range(self.start_date, self.end_date)


# ── 各指標の計算 ───────────────────────────────────────────────

def shot_facts(cur_tasks, prev_tasks, period):
    completed = sum(1 for t in cur_tasks if isinstance(t, dict) and period.has_ts(t.get('completedAt')))
    created = sum(1 for t in cur_tasks if isinstance(t, dict) and period.has_ts(t.get('createdAt')))
    return {
        'completed': completed,
        'created': created,
        'overdue_now': count_overdue(cur_tasks, period.end_date),
        'overdue_prev': count_overdue(prev_tasks, period.start_date),
    }


def count_overdue(tasks, as_of):
    """as_of 時点で未完了（todo/pending）かつ期日超過のShot件数。"""
    n = 0
    for t in tasks:
        if not isinstance(t, dict) or t.get('status') not in SHOT_OPEN:
            continue
        due = H.parse_ymd(t.get('dueDate'))
        if due is not None and due < as_of:
            n += 1
    return n


def lectica_facts(cur_exps, prev_exps, cur_logs, period):
    logs = [l for l in cur_logs if isinstance(l, dict) and period.has_date(l.get('date'))]
    logged_days = {local_date(l.get('date')) for l in logs}

    prev_status = {e.get('id'): e.get('status') for e in prev_exps if isinstance(e, dict)}
    newly_completed = 0
    for e in cur_exps:
        if not isinstance(e, dict) or e.get('status') != 'completed':
            continue
        if prev_status.get(e.get('id')) != 'completed':   # 先週まだcompletedでなかった＝今週完了
            newly_completed += 1

    return {
        'logged_days': len(logged_days),
        'logs': len(logs),
        'completed_experiments': newly_completed,
        'active_now': sum(1 for e in cur_exps if isinstance(e, dict) and e.get('status') == 'active'),
    }


def oneday_facts(cur_logs, period):
    logged = {local_date(l.get('date')) for l in cur_logs
              if isinstance(l, dict) and period.has_date(l.get('date'))}
    missing = [d.isoformat() for d in period.days() if d not in logged]
    return {'logged_days': len(logged), 'missing_days': missing}


def top10_contact_facts(profiles, su_persons, period):
    ids, unlinked = H.top10_ids(profiles, su_persons)
    by_id = {p.get('id'): p for p in profiles if isinstance(p, dict)}

    contacted, not_contacted = 0, []
    for pid in ids:
        p = by_id.get(pid) or {}
        if period.has_date(p.get('lastContactDate')):
            contacted += 1
        else:
            not_contacted.append(H.get_name(p) or '(名前空)')
    # ヒトメモに紐づかないTop10は接触判定できない＝未接触として名前を出す（黙って落とさない）
    not_contacted.extend('{}（ヒトメモ未紐づけ）'.format(n) for n in unlinked)

    return {
        'contacted': contacted,
        'total': len(ids) + len(unlinked),
        'not_contacted_names': sorted(not_contacted),
    }


def has_experience_log(profile, period):
    """期間内に「経験」系のchangeLogがあるか。"""
    for l in (profile.get('changeLog') or []):
        if not isinstance(l, dict) or not period.has_date(l.get('date')):
            continue
        if '経験' in '{} {}'.format(l.get('type', ''), l.get('text', '')):
            return True
    return False


def next_experience_facts(profiles, period):
    have = [p for p in profiles
            if isinstance(p, dict) and str(H.field_val(p.get('nextExperience')) or '').strip()]
    return {
        'set': len(have),
        'executed_this_week': sum(1 for p in have if has_experience_log(p, period)),
    }


def is_sheet_artifact_updated_at(item):
    """updatedAt がシート取り込み由来（＝そのアイテムの予定日そのもの）か。

    シート取り込みのアイテムは updatedAt に "<date>T00:00:00.000Z" が入り、実編集の時刻ではない。
    これを活動とみなすと、未来の予定日（例 2030-12-31）が「最終活動日」になってしまう。
    """
    d, u = item.get('date'), item.get('updatedAt')
    if not d or not u:
        return False
    u = str(u)
    return u.startswith(str(d)) and 'T00:00:00' in u


def item_activity_dates(item, end_date):
    """アイテムが示す「実際の活動日」。未来日は活動ではないので捨てる。"""
    out = []
    if not is_sheet_artifact_updated_at(item):
        d = local_date(item.get('updatedAt'))     # 実編集のタイムスタンプ
        if d and d <= end_date:
            out.append(d)
    if item.get('status') == '完了':               # 完了イベントは、その日に起きた活動
        d = local_date(item.get('date'))
        if d and d <= end_date:
            out.append(d)
    return out


def project_last_activity(p, end_date):
    """プロジェクトの最終活動日。無ければ None。"""
    stamps = []
    d = local_date(p.get('updatedAt'))
    if d and d <= end_date:
        stamps.append(d)
    for fld in PROJECT_ITEM_FIELDS:
        for it in (p.get(fld) or []):
            if isinstance(it, dict):
                stamps.extend(item_activity_dates(it, end_date))
    return max(stamps) if stamps else None


def project_facts(projects, period):
    """重要度A/高 かつ 期間内に活動が無いPJ。

    注意: Shotタスクにプロジェクト参照フィールドが無いため「対応Shot完了」は機械計算できない。
    活動シグナルは projectOS 側のみ（本体updatedAt / アイテムの実編集updatedAt / 完了イベントの日付）。
    """
    stale = []
    for p in projects:
        if not isinstance(p, dict) or p.get('priority') not in IMPORTANT_PRIORITY:
            continue
        last = project_last_activity(p, period.end_date)
        if last is not None and period.start_date <= last <= period.end_date:
            continue  # 期間内に活動あり
        stale.append({
            'name': p.get('name') or '(無名PJ)',
            'days_stale': (period.end_date - last).days if last else None,
        })
    stale.sort(key=lambda x: (x['days_stale'] is None, -(x['days_stale'] or 0)))
    return stale


def hitomemo_facts(profiles, period):
    n = 0
    for p in profiles:
        if not isinstance(p, dict):
            continue
        n += sum(1 for l in (p.get('changeLog') or [])
                 if isinstance(l, dict) and period.has_date(l.get('date')))
    return {'changelog_entries_this_week': n}


# ── 統合 ───────────────────────────────────────────────────────

def compute_facts(cur, prev):
    period = Period(prev.get('savedAt'), cur.get('savedAt'))

    cur_shot = H.as_list(cur.get('shotTaskOS'), 'tasks')
    prev_shot = H.as_list(prev.get('shotTaskOS'), 'tasks')
    cur_exps = H.as_list(cur.get('lecticaExperiments'), 'items', 'experiments')
    prev_exps = H.as_list(prev.get('lecticaExperiments'), 'items', 'experiments')
    cur_lg = H.as_list(cur.get('lecticaLogs'), 'logs', 'items')
    cur_od = H.as_list(cur.get('onedayLogs'), 'logs')
    profiles = H.as_list(cur.get('hitomemo'), 'profiles')
    su = H.as_list(cur.get('socialUniverse'), 'persons')
    projects = H.as_list(cur.get('projectOS'), 'projects')

    return {
        'period': {'from': period.start_date.isoformat(), 'to': period.end_date.isoformat()},
        'shot': shot_facts(cur_shot, prev_shot, period),
        'lectica': lectica_facts(cur_exps, prev_exps, cur_lg, period),
        'oneday': oneday_facts(cur_od, period),
        'top10_contact': top10_contact_facts(profiles, su, period),
        'next_experience': next_experience_facts(profiles, period),
        'projects': {'important_no_activity': project_facts(projects, period)},
        'hitomemo': hitomemo_facts(profiles, period),
        '_meta': {
            'generated_by': 'tools/weekly_facts.py',
            'period_rule': '時刻付きは(先週savedAt, 今週savedAt]、日付のみは[先週日付, 今週日付]で判定',
            'caveats': [
                'Shotタスクにプロジェクト参照フィールドが無いため、'
                'projects.important_no_activity は「対応Shot完了」を判定に含めていない',
                'シート取り込みアイテムのupdatedAtは予定日そのもの（実編集時刻ではない）ため、'
                'PJの活動判定からは除外している',
            ],
        },
    }


def render_markdown(f):
    p = f['period']
    L = []
    L.append('## 今週の事実差分（{} 〜 {}）'.format(p['from'], p['to']))
    L.append('')
    L.append('| 指標 | 値 |')
    L.append('|------|----|')
    s = f['shot']
    L.append('| Shot 完了 | {} 件 |'.format(s['completed']))
    L.append('| Shot 新規 | {} 件 |'.format(s['created']))
    L.append('| Shot 期限超過 | {} 件（先週 {} 件・{:+d}）|'.format(
        s['overdue_now'], s['overdue_prev'], s['overdue_now'] - s['overdue_prev']))
    lc = f['lectica']
    L.append('| Lectica 記録日数 | {} 日（ログ {} 件）|'.format(lc['logged_days'], lc['logs']))
    L.append('| Lectica 今週完了した実験 | {} 件 |'.format(lc['completed_experiments']))
    L.append('| Lectica 実験中 | {} 件 |'.format(lc['active_now']))
    od = f['oneday']
    L.append('| 1day 記録日数 | {} 日 |'.format(od['logged_days']))
    L.append('| 1day 欠落日 | {} |'.format(', '.join(od['missing_days']) if od['missing_days'] else 'なし'))
    tc = f['top10_contact']
    L.append('| Top10 接触 | {} / {} 人 |'.format(tc['contacted'], tc['total']))
    ne = f['next_experience']
    L.append('| 次に渡す経験 実行 | {} / {} 人 |'.format(ne['executed_this_week'], ne['set']))
    L.append('| ヒトメモ changeLog | {} 件 |'.format(f['hitomemo']['changelog_entries_this_week']))
    L.append('')

    if tc['not_contacted_names']:
        L.append('**Top10 未接触**: ' + ' / '.join(tc['not_contacted_names']))
        L.append('')
    stale = f['projects']['important_no_activity']
    if stale:
        L.append('**重要PJで今週動きなし**:')
        for x in stale:
            days = '{}日'.format(x['days_stale']) if x['days_stale'] is not None else '記録なし'
            L.append('- {}（最終活動から {}）'.format(x['name'], days))
    else:
        L.append('**重要PJで今週動きなし**: なし')
    L.append('')
    for c in f['_meta']['caveats']:
        L.append('> 注: {}'.format(c))
    return '\n'.join(L)


def load_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser(description='週次「事実の差分」を機械計算して aix_weekly_facts.json を出力')
    ap.add_argument('current', help='今週のbackup.json')
    ap.add_argument('previous', help='先週のスナップショット.json')
    ap.add_argument('--out', default='aix_weekly_facts.json', help='出力先（既定: ./aix_weekly_facts.json）')
    args = ap.parse_args()

    try:
        cur = load_json(args.current)
        prev = load_json(args.previous)
    except FileNotFoundError as e:
        print('ファイルが見つかりません: {}'.format(e.filename))
        return 2
    except json.JSONDecodeError as e:
        print('JSONとして読めません: {}'.format(e))
        return 2

    try:
        facts = compute_facts(cur, prev)
    except ValueError as e:
        print('エラー: {}'.format(e))
        return 2

    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(facts, fh, ensure_ascii=False, indent=2)

    print(render_markdown(facts))
    print()
    print('→ {} を出力しました。Coworkの作業フォルダにコピーしてください。'.format(args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
