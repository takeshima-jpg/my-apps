#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myapps データ健全性チェック（9項目）

使い方:
    python tools/check_backup_health.py <myapps-all-backup-*.json のパス>

終了コード: 異常なし=0 / 警告あり=1
すべて過去に実際に起きた事故の再発検知を目的にしている。標準ライブラリのみ。
"""

import sys
import json
import re
import unicodedata
from datetime import datetime, timezone, date, timedelta

# Windowsコンソール(cp932)でも絵文字・日本語を出力できるよう標準出力をUTF-8化
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ── 共通ユーティリティ ──────────────────────────────────────────

def as_list(v, *keys):
    """配列そのもの / {キー: 配列} のどちらでもリストで返す。取れなければ []。"""
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        for k in keys:
            if isinstance(v.get(k), list):
                return v[k]
    return []


def parse_iso(s):
    """ISO日時（末尾Z対応）を aware datetime に。失敗時 None。"""
    if not s:
        return None
    s = str(s).strip()
    try:
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def parse_ymd(s):
    """先頭10文字を YYYY-MM-DD として date に。失敗時 None。"""
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def norm_name(s):
    """人物名の正規化：括弧注記除去・空白除去・NFKC・小文字化。"""
    if isinstance(s, dict):
        s = s.get('value', '')
    if not s:
        return ''
    s = unicodedata.normalize('NFKC', str(s))
    s = re.sub(r'[（(【\[〔｛{].*?[）)】\]〕｝}]', '', s)  # 括弧注記を除去
    s = re.sub(r'\s+', '', s)
    return s.lower()


def get_name(p):
    """プロフィールの name（文字列 or {value}）を素の文字列で返す。"""
    n = p.get('name') if isinstance(p, dict) else None
    if isinstance(n, dict):
        return n.get('value', '') or ''
    return n or ''


def field_val(v):
    """AI更新で {value:..} 形式になり得る欄を素の値に。"""
    if isinstance(v, dict):
        return v.get('value', '')
    return v


def link_key(s):
    """SU⇔ヒトメモの名前フォールバック照合キー（正規化に加えSU側の敬称「さん」も落とす）。"""
    return re.sub(r'さん$', '', norm_name(s))


def top10_ids(profiles, su_persons):
    """socialUniverseでisTop10=trueの人物に対応するヒトメモidの集合と、紐づかなかったSU人物名。

    紐づけはSU本体と同じ hitoId優先・名前フォールバック（social-universe の reflectToHitomemo）。
    """
    by_id = {}
    by_name = {}
    for p in profiles:
        if not isinstance(p, dict):
            continue
        if p.get('id'):
            by_id[p['id']] = p
        k = link_key(get_name(p))
        if k and k not in by_name:
            by_name[k] = p

    ids, unlinked = set(), []
    for su in su_persons:
        if not isinstance(su, dict) or not su.get('isTop10'):
            continue
        p = by_id.get(su.get('hitoId')) or by_name.get(link_key(su.get('name')))
        if p:
            ids.add(p.get('id'))
        else:
            unlinked.append(su.get('name') or '(名前空)')
    return ids, unlinked


# ── 各チェック（ok, 見出し行群）を返す ──────────────────────────

def check_freshness(data):
    dt = parse_iso(data.get('savedAt'))
    if dt is None:
        return False, ['⚠ 鮮度: savedAt が読めない（同期状態を確認）']
    now = datetime.now(timezone.utc)
    hours = (now - dt).total_seconds() / 3600
    local = dt.astimezone()
    stamp = local.strftime('%Y-%m-%dT%H:%M')
    ago = f'{hours:.0f}h前' if hours >= 1 else f'{hours*60:.0f}分前'
    if hours > 24:
        return False, [f'⚠ 鮮度: savedAt {stamp}（{ago}）— 24時間以上前。同期が止まっている可能性']
    return True, [f'✅ 鮮度: savedAt {stamp}（{ago}）']


def check_hitomemo_id(profiles):
    seen = {}
    dup = {}
    for p in profiles:
        pid = p.get('id') if isinstance(p, dict) else None
        if pid is None:
            continue
        if pid in seen:
            dup.setdefault(pid, [seen[pid]]).append(get_name(p))
        else:
            seen[pid] = get_name(p)
    if dup:
        lines = ['⚠ ヒトメモID衝突: {}件（1件削除で複数人が消える前兆）'.format(len(dup))]
        for pid, names in list(dup.items())[:10]:
            lines.append('    id={} : {}'.format(pid, ' / '.join(n or '(名前空)' for n in names)))
        return False, lines
    return True, ['✅ ID衝突: なし']


def check_hitomemo_dupname(profiles):
    groups = {}
    for p in profiles:
        nm = get_name(p)
        key = norm_name(nm)
        if not key:
            continue
        groups.setdefault(key, []).append(nm)
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    if dups:
        lines = ['⚠ ヒトメモ同名重複: {}組'.format(len(dups))]
        for k, v in list(dups.items())[:10]:
            lines.append('    {} ×{}'.format(v[0], len(v)))
        return False, lines
    return True, ['✅ 同名重複: なし']


def check_shot_stale(tasks):
    today = date.today()
    stale = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        if t.get('status') != 'todo':
            continue
        due = parse_ymd(t.get('dueDate'))
        if due is None:
            continue
        days = (today - due).days
        if days >= 3:
            stale.append((days, t))
    if not stale:
        return True, ['✅ Shot滞留: なし（todo かつ期限3日超過なし）']
    stale.sort(key=lambda x: -x[0])
    lines = ['⚠ Shot滞留: {}件（status=todo かつ期限3日以上超過）'.format(len(stale))]
    for days, t in stale[:12]:
        lines.append('    {}日超過 [{}] {}'.format(days, t.get('category', '-'), (t.get('title') or '(無題)')[:40]))
    # 同一Lectica実験の重複滞留を強調
    lect = {}
    for days, t in stale:
        cat = t.get('category', '')
        title = (t.get('title') or '')
        if cat == 'Lectica' or 'Lectica実験' in title:
            key = t.get('experimentId') or t.get('expId') or title
            lect.setdefault(key, 0)
            lect[key] += 1
    heavy = {k: c for k, c in lect.items() if c >= 2}
    for k, c in heavy.items():
        lines.append('    ★ Lectica重複滞留: 「{}」が {}件 todo'.format(str(k)[:40], c))
    return False, lines


def check_lectica_stale(experiments, logs):
    today = date.today()
    last = {}
    for l in logs:
        if not isinstance(l, dict):
            continue
        eid = l.get('experimentId')
        d = parse_ymd(l.get('date'))
        if not eid or d is None:
            continue
        if eid not in last or d > last[eid]:
            last[eid] = d
    stale = []
    for e in experiments:
        if not isinstance(e, dict) or e.get('status') != 'active':
            continue
        eid = e.get('id')
        d = last.get(eid)
        if d is None or (today - d).days > 14:
            age = '記録なし' if d is None else '{}日前'.format((today - d).days)
            stale.append('{}：{}（最終ログ {}）'.format(eid, (e.get('title') or '')[:30], age))
    if stale:
        lines = ['⚠ Lectica鮮度: active なのに直近14日ログ無しが {}件'.format(len(stale))]
        for s in stale[:12]:
            lines.append('    ' + s)
        return False, lines
    return True, ['✅ Lectica鮮度: active実験はすべて直近14日にログあり']


def check_mechanism_idle(profiles, su_persons):
    """socialUniverseでisTop10=trueの人物に限定して判定する。
    Top10外の過去のnextExperience設定はノイズなので数えない。"""
    ids, unlinked = top10_ids(profiles, su_persons)
    if not ids and not unlinked:
        return True, ['ℹ 仕組みの空転: socialUniverseにTop10設定が無いためスキップ']

    today = date.today()
    idle = []
    for p in profiles:
        if not isinstance(p, dict) or p.get('id') not in ids:
            continue
        nx = field_val(p.get('nextExperience'))
        if not nx or not str(nx).strip():
            continue
        recent = False
        for l in (p.get('changeLog') or []):
            if not isinstance(l, dict):
                continue
            d = parse_ymd(l.get('date'))
            if d is None or (today - d).days > 30:
                continue
            blob = '{} {}'.format(l.get('type', ''), l.get('text', ''))
            if '経験' in blob:
                recent = True
                break
        if not recent:
            idle.append(get_name(p))

    total = len(ids) + len(unlinked)
    if idle:
        lines = ['⚠ 仕組みの空転: Top10のうち nextExperience設定済みだが直近30日に経験ログ無し {}人（Top10 {}人中）'.format(len(idle), total)]
        lines.append('    ' + ' / '.join((n or '(名前空)') for n in idle[:15]))
    else:
        lines = ['✅ 仕組みの空転: なし（Top10 {}人中）'.format(total)]
    if unlinked:
        # 対象から漏れている＝チェックが黙って過少になるので必ず表に出す
        lines.append('    ⚠ SU Top10のうち {}人はヒトメモに紐づかず対象外: {}'.format(len(unlinked), ' / '.join(unlinked[:10])))
    return (not idle and not unlinked), lines


def check_oneday_gap(logs):
    today = date.today()
    dates = [parse_ymd(l.get('date')) for l in logs if isinstance(l, dict)]
    dates = [d for d in dates if d]
    if not dates:
        return False, ['⚠ 1dayログ: 日付付きログが無い']
    latest = max(dates)
    gap = (today - latest).days
    if gap >= 2:
        return False, ['⚠ 1dayログ欠落: 最新 {} から {}日空いている'.format(latest.isoformat(), gap)]
    return True, ['✅ 1dayログ: 最新 {}（{}日前）'.format(latest.isoformat(), gap)]


def check_required_keys(data):
    required = [
        'savedAt', 'shotTaskOS', 'routineOS', 'projectOS', 'list100',
        'onedayLogs', 'onedayReviews', 'kosoLog', 'socialUniverse', 'hitomemo',
        'lecticaExperiments', 'lecticaLogs', 'aixReviewWeekly', 'aixReviewMonthly',
    ]
    missing = [k for k in required if data.get(k) is None]
    if 'reflectOS' in data and data.get('reflectOS') is None:
        missing.append('reflectOS')
    if missing:
        return False, ['⚠ 必須キー欠落: {} が null（バックアップ収集漏れの疑い）'.format(' / '.join(missing))]
    return True, ['✅ 必須キー: 欠落なし']


def check_holidays(data):
    ro = data.get('routineOS')
    holidays = ro.get('holidays') if isinstance(ro, dict) else None
    if holidays is None:
        return False, ['⚠ routineOS.holidays: null（祝日がバックアップされていない）']
    return True, ['✅ routineOS.holidays: あり（{}件）'.format(len(holidays) if hasattr(holidays, '__len__') else '?')]


# ── メイン ──────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        print('使い方: python tools/check_backup_health.py <myapps-all-backup-*.json>')
        return 2
    path = sys.argv[1]
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print('ファイルが見つかりません: {}'.format(path))
        return 2
    except json.JSONDecodeError as e:
        print('JSONとして読めません: {}'.format(e))
        return 2

    profiles = as_list(data.get('hitomemo'), 'profiles')
    shot_tasks = as_list(data.get('shotTaskOS'), 'tasks')
    oneday_logs = as_list(data.get('onedayLogs'), 'logs')
    experiments = as_list(data.get('lecticaExperiments'), 'items', 'experiments')
    lectica_logs = as_list(data.get('lecticaLogs'), 'logs', 'items')
    su_persons = as_list(data.get('socialUniverse'), 'persons')

    checks = [
        ('鮮度', lambda: check_freshness(data)),
        ('ヒトメモID衝突', lambda: check_hitomemo_id(profiles)),
        ('ヒトメモ同名重複', lambda: check_hitomemo_dupname(profiles)),
        ('Shot滞留', lambda: check_shot_stale(shot_tasks)),
        ('Lectica鮮度', lambda: check_lectica_stale(experiments, lectica_logs)),
        ('仕組みの空転', lambda: check_mechanism_idle(profiles, su_persons)),
        ('1dayログ欠落', lambda: check_oneday_gap(oneday_logs)),
        ('必須キー欠落', lambda: check_required_keys(data)),
        ('routineOS.holidays', lambda: check_holidays(data)),
    ]

    today = date.today().isoformat()
    print('== myapps backup health ({}) =='.format(today))
    print('   対象: {}'.format(path))
    warn = 0
    for name, fn in checks:
        try:
            ok, lines = fn()
        except Exception as e:
            ok, lines = False, ['⚠ {}: 判定中にエラー（{}）'.format(name, e)]
        if not ok:
            warn += 1
        for ln in lines:
            print(ln)
    print('-' * 40)
    print('警告 {}件 / 検査 {}項目'.format(warn, len(checks)))
    return 1 if warn else 0


if __name__ == '__main__':
    sys.exit(main())
