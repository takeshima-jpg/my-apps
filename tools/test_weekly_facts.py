#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly_facts.py のユニットテスト（架空の2スナップショット）。

    python tools/test_weekly_facts.py

期間は 先週 2026-07-05T00:00Z 〜 今週 2026-07-12T00:00Z。
JST(+9)に変換されるため、期間の日付は 2026-07-05 〜 2026-07-12。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weekly_facts as W  # noqa: E402

PREV_SAVED = '2026-07-05T00:00:00.000Z'   # JST 2026-07-05 09:00
CUR_SAVED = '2026-07-12T00:00:00.000Z'    # JST 2026-07-12 09:00


def shot(title, status, completed_at=None, created_at=None, due=None):
    return {'id': title, 'title': title, 'status': status,
            'completedAt': completed_at, 'createdAt': created_at, 'dueDate': due}


def profile(pid, name, last_contact=None, next_exp='', change_log=None):
    return {'id': pid, 'name': name, 'lastContactDate': last_contact,
            'nextExperience': next_exp, 'changeLog': change_log or []}


def base_snapshot(saved_at, **kw):
    snap = {
        'savedAt': saved_at,
        'shotTaskOS': [], 'lecticaExperiments': [], 'lecticaLogs': [],
        'onedayLogs': [], 'hitomemo': [], 'socialUniverse': [],
        'projectOS': {'projects': []},
    }
    snap.update(kw)
    return snap


class TestPeriod(unittest.TestCase):
    def test_period_is_local_dates(self):
        f = W.compute_facts(base_snapshot(CUR_SAVED), base_snapshot(PREV_SAVED))
        self.assertEqual(f['period'], {'from': '2026-07-05', 'to': '2026-07-12'})

    def test_reversed_order_is_rejected(self):
        with self.assertRaises(ValueError):
            W.Period(CUR_SAVED, PREV_SAVED)   # 先週/今週が逆


class TestShotCompleted(unittest.TestCase):
    """完了数の計算"""

    def setUp(self):
        self.cur = base_snapshot(CUR_SAVED, shotTaskOS=[
            shot('期間内に完了', 'done', completed_at='2026-07-08T03:00:00.000Z'),
            shot('期間内に完了2', 'done', completed_at='2026-07-11T23:00:00.000Z'),
            shot('先週の完了（範囲外）', 'done', completed_at='2026-07-04T03:00:00.000Z'),
            shot('境界=先週savedAtちょうど（範囲外）', 'done', completed_at=PREV_SAVED),
            shot('境界=今週savedAtちょうど（範囲内）', 'done', completed_at=CUR_SAVED),
            shot('未完了', 'todo', due='2026-07-01'),
            shot('却下はcompletedAt無し', 'rejected'),
        ])
        self.prev = base_snapshot(PREV_SAVED)

    def test_completed_counts_only_in_period(self):
        f = W.compute_facts(self.cur, self.prev)
        # 期間内2件 + 今週savedAtちょうど1件 = 3件（先週savedAtちょうどは半開区間で除外）
        self.assertEqual(f['shot']['completed'], 3)

    def test_created_counts_only_in_period(self):
        cur = base_snapshot(CUR_SAVED, shotTaskOS=[
            shot('今週作成', 'todo', created_at='2026-07-07T00:00:00.000Z'),
            shot('先週作成', 'todo', created_at='2026-06-30T00:00:00.000Z'),
        ])
        f = W.compute_facts(cur, base_snapshot(PREV_SAVED))
        self.assertEqual(f['shot']['created'], 1)

    def test_overdue_now_and_prev(self):
        cur = base_snapshot(CUR_SAVED, shotTaskOS=[
            shot('超過todo', 'todo', due='2026-07-01'),
            shot('超過pending', 'pending', due='2026-07-02'),
            shot('未来todo', 'todo', due='2026-12-31'),
            shot('超過だがdone', 'done', due='2026-07-01', completed_at='2026-07-06T00:00:00.000Z'),
            shot('超過だがrejected', 'rejected', due='2026-07-01'),
        ])
        prev = base_snapshot(PREV_SAVED, shotTaskOS=[
            shot('先週時点で超過', 'todo', due='2026-07-01'),
            # 先週(7/5)時点ではまだ期限内 → 先週の超過に数えない
            shot('先週はまだ期限内', 'todo', due='2026-07-08'),
        ])
        f = W.compute_facts(cur, prev)
        self.assertEqual(f['shot']['overdue_now'], 2)    # todo + pending のみ
        self.assertEqual(f['shot']['overdue_prev'], 1)


class TestTop10Contact(unittest.TestCase):
    """接触数の計算"""

    def test_contacted_and_not_contacted(self):
        profiles = [
            profile('1', '山田 太郎', last_contact='2026-07-07'),   # 期間内 → 接触
            profile('2', '佐藤 花子', last_contact='2026-06-20'),   # 期間外 → 未接触
            profile('3', '鈴木 一郎', last_contact=None),           # 記録なし → 未接触
            profile('4', 'Top10外 次郎', last_contact='2026-07-07'),  # Top10外 → 対象外
        ]
        su = [
            {'name': '山田さん', 'hitoId': '1', 'isTop10': True},
            {'name': '佐藤さん', 'hitoId': '2', 'isTop10': True},
            {'name': '鈴木さん', 'hitoId': '3', 'isTop10': True},
            {'name': '次郎さん', 'hitoId': '4', 'isTop10': False},
        ]
        f = W.compute_facts(base_snapshot(CUR_SAVED, hitomemo=profiles, socialUniverse=su),
                            base_snapshot(PREV_SAVED))
        tc = f['top10_contact']
        self.assertEqual(tc['total'], 3)
        self.assertEqual(tc['contacted'], 1)
        self.assertEqual(tc['not_contacted_names'], ['佐藤 花子', '鈴木 一郎'])

    def test_unlinked_top10_is_surfaced_not_dropped(self):
        """ヒトメモに紐づかないTop10は、黙って落とさず未接触として名前を出す"""
        su = [{'name': '知らない人', 'hitoId': 'none', 'isTop10': True}]
        f = W.compute_facts(base_snapshot(CUR_SAVED, hitomemo=[], socialUniverse=su),
                            base_snapshot(PREV_SAVED))
        tc = f['top10_contact']
        self.assertEqual(tc['total'], 1)
        self.assertEqual(tc['contacted'], 0)
        self.assertEqual(tc['not_contacted_names'], ['知らない人（ヒトメモ未紐づけ）'])


class TestOnedayMissingDays(unittest.TestCase):
    """欠落日の計算"""

    def test_missing_days(self):
        logs = [
            {'date': '2026-07-05'}, {'date': '2026-07-06'},
            {'date': '2026-07-06'},                       # 同日重複 → 1日として数える
            {'date': '2026-07-09'}, {'date': '2026-07-12'},
            {'date': '2026-06-30'},                       # 期間外 → 無視
        ]
        f = W.compute_facts(base_snapshot(CUR_SAVED, onedayLogs=logs), base_snapshot(PREV_SAVED))
        od = f['oneday']
        self.assertEqual(od['logged_days'], 4)
        self.assertEqual(od['missing_days'], ['2026-07-07', '2026-07-08', '2026-07-10', '2026-07-11'])

    def test_all_days_missing_when_no_logs(self):
        f = W.compute_facts(base_snapshot(CUR_SAVED), base_snapshot(PREV_SAVED))
        self.assertEqual(f['oneday']['logged_days'], 0)
        self.assertEqual(len(f['oneday']['missing_days']), 8)   # 7/5〜7/12 の8日


class TestLectica(unittest.TestCase):
    def test_logged_days_logs_and_newly_completed(self):
        cur = base_snapshot(CUR_SAVED,
            lecticaExperiments=[
                {'id': 'L001', 'status': 'completed'},   # 先週active → 今週完了
                {'id': 'L002', 'status': 'completed'},   # 先週から完了 → 数えない
                {'id': 'L003', 'status': 'active'},
                {'id': 'L004', 'status': 'not_started'},
            ],
            lecticaLogs=[
                {'experimentId': 'L001', 'date': '2026-07-06'},
                {'experimentId': 'L003', 'date': '2026-07-06'},   # 同日 → 1日
                {'experimentId': 'L003', 'date': '2026-07-09'},
                {'experimentId': 'L003', 'date': '2026-06-01'},   # 期間外
            ])
        prev = base_snapshot(PREV_SAVED, lecticaExperiments=[
            {'id': 'L001', 'status': 'active'},
            {'id': 'L002', 'status': 'completed'},
            {'id': 'L003', 'status': 'active'},
        ])
        lc = W.compute_facts(cur, prev)['lectica']
        self.assertEqual(lc['logs'], 3)
        self.assertEqual(lc['logged_days'], 2)
        self.assertEqual(lc['completed_experiments'], 1)
        self.assertEqual(lc['active_now'], 1)

    def test_experiment_new_this_week_and_already_completed(self):
        """先週スナップショットに存在しない実験が completed なら今週完了として数える"""
        cur = base_snapshot(CUR_SAVED, lecticaExperiments=[{'id': 'L099', 'status': 'completed'}])
        prev = base_snapshot(PREV_SAVED, lecticaExperiments=[])
        self.assertEqual(W.compute_facts(cur, prev)['lectica']['completed_experiments'], 1)


class TestNextExperienceAndHitomemo(unittest.TestCase):
    def test_executed_counts_experience_logs_in_period(self):
        profiles = [
            profile('1', 'A', next_exp='任せる', change_log=[{'date': '2026-07-07', 'type': '経験', 'text': '任せた'}]),
            profile('2', 'B', next_exp='任せる', change_log=[{'date': '2026-06-01', 'type': '経験', 'text': '古い'}]),
            profile('3', 'C', next_exp='任せる', change_log=[{'date': '2026-07-07', 'type': '打合せ', 'text': '雑談'}]),
            profile('4', 'D', next_exp='', change_log=[{'date': '2026-07-07', 'type': '経験', 'text': '対象外'}]),
        ]
        f = W.compute_facts(base_snapshot(CUR_SAVED, hitomemo=profiles), base_snapshot(PREV_SAVED))
        self.assertEqual(f['next_experience']['set'], 3)
        self.assertEqual(f['next_experience']['executed_this_week'], 1)
        # changeLog件数は期間内のものだけ（3件: A,C,D の 7/7）
        self.assertEqual(f['hitomemo']['changelog_entries_this_week'], 3)


class TestProjects(unittest.TestCase):
    def test_important_projects_without_activity(self):
        projects = [
            # 重要・期間内に本体更新あり → 除外
            {'name': '動いてるPJ', 'priority': '高', 'updatedAt': '2026-07-08', 'events': []},
            # 重要・本体は古いがイベントが期間内に更新 → 除外
            {'name': 'イベントが動いたPJ', 'priority': 'A', 'updatedAt': '2026-05-01',
             'events': [{'updatedAt': '2026-07-09T00:00:00.000Z'}]},
            # 重要・活動なし → 検出（7/12 - 6/12 = 30日）
            {'name': '止まってるPJ', 'priority': '高', 'updatedAt': '2026-06-12', 'events': []},
            # 重要度が中 → 対象外
            {'name': '重要でないPJ', 'priority': '中', 'updatedAt': '2026-01-01', 'events': []},
        ]
        f = W.compute_facts(base_snapshot(CUR_SAVED, projectOS={'projects': projects}),
                            base_snapshot(PREV_SAVED))
        stale = f['projects']['important_no_activity']
        self.assertEqual([x['name'] for x in stale], ['止まってるPJ'])
        self.assertEqual(stale[0]['days_stale'], 30)

    def test_project_without_any_timestamp(self):
        projects = [{'name': '記録なしPJ', 'priority': '高'}]
        f = W.compute_facts(base_snapshot(CUR_SAVED, projectOS={'projects': projects}),
                            base_snapshot(PREV_SAVED))
        stale = f['projects']['important_no_activity']
        self.assertEqual(stale[0]['days_stale'], None)

    def test_sheet_imported_future_item_is_not_activity(self):
        """回帰: シート取り込みのupdatedAtは予定日そのもの。
        未来予定を最終活動日として拾うと days_stale が負になっていた。"""
        projects = [{
            'name': '未来の予定だけPJ', 'priority': '高', 'updatedAt': '2026-06-12',
            'events': [{'date': '2026-09-30', 'updatedAt': '2026-09-30T00:00:00.000Z', 'status': '未着手'}],
            'forks': [{'date': '2030-12-31', 'updatedAt': '2030-12-31T00:00:00.000Z', 'status': 'future'}],
        }]
        f = W.compute_facts(base_snapshot(CUR_SAVED, projectOS={'projects': projects}),
                            base_snapshot(PREV_SAVED))
        stale = f['projects']['important_no_activity']
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]['days_stale'], 30)   # 本体updatedAt 6/12 が最終活動 → 負にならない
        self.assertGreaterEqual(stale[0]['days_stale'], 0)

    def test_sheet_artifact_in_period_is_not_activity(self):
        """期間内の予定日でも、シート取り込み由来なら『動いた』とは数えない"""
        projects = [{
            'name': '予定日が期間内なだけPJ', 'priority': '高', 'updatedAt': '2026-06-12',
            'events': [{'date': '2026-07-08', 'updatedAt': '2026-07-08T00:00:00.000Z', 'status': '未着手'}],
        }]
        f = W.compute_facts(base_snapshot(CUR_SAVED, projectOS={'projects': projects}),
                            base_snapshot(PREV_SAVED))
        self.assertEqual([x['name'] for x in f['projects']['important_no_activity']],
                         ['予定日が期間内なだけPJ'])

    def test_real_edit_timestamp_counts_as_activity(self):
        """実編集のタイムスタンプ（予定日と一致しない時刻付き）は活動として数える"""
        projects = [{
            'name': '実編集ありPJ', 'priority': '高', 'updatedAt': '2026-06-12',
            'events': [{'date': '2026-07-03', 'updatedAt': '2026-07-08T12:10:08.413Z', 'status': '完了'}],
        }]
        f = W.compute_facts(base_snapshot(CUR_SAVED, projectOS={'projects': projects}),
                            base_snapshot(PREV_SAVED))
        self.assertEqual(f['projects']['important_no_activity'], [])

    def test_completed_event_dated_in_period_counts_as_activity(self):
        """完了イベントは、その日に起きた活動として数える"""
        projects = [{
            'name': '完了イベントありPJ', 'priority': '高', 'updatedAt': '2026-06-12',
            'events': [{'date': '2026-07-07', 'updatedAt': '2026-07-07T00:00:00.000Z', 'status': '完了'}],
        }]
        f = W.compute_facts(base_snapshot(CUR_SAVED, projectOS={'projects': projects}),
                            base_snapshot(PREV_SAVED))
        self.assertEqual(f['projects']['important_no_activity'], [])


class TestRenderMarkdown(unittest.TestCase):
    def test_markdown_contains_period_and_numbers(self):
        f = W.compute_facts(base_snapshot(CUR_SAVED, shotTaskOS=[
            shot('完了', 'done', completed_at='2026-07-08T03:00:00.000Z')]), base_snapshot(PREV_SAVED))
        md = W.render_markdown(f)
        self.assertIn('2026-07-05 〜 2026-07-12', md)
        self.assertIn('| Shot 完了 | 1 件 |', md)


if __name__ == '__main__':
    unittest.main(verbosity=2)
