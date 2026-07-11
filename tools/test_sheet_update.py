#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sheet_update.py の純粋ヘルパーのユニットテスト（API非依存部分）。

    python tools/test_sheet_update.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheet_update as S  # noqa: E402

HEADER = ['ID', 'テーマ', '種別', '期日', '状態', 'イベント', '担当', '対象', '施策', 'ゴール（狙い）', '結果']
SHEET = [
    ['PJ名', 'テストPJ'],
    ['ゴール', 'ゴールG'],
    [],
    HEADER,
    ['11', '1', '', '2026/06/20', '完了', 'イベントA'],
    ['21', '2', '分岐', '2026/08/01', '未着手', '分岐B', '', '対象Y'],
]


class TestHelpers(unittest.TestCase):
    def test_col_letter(self):
        self.assertEqual(S.col_letter(0), 'A')
        self.assertEqual(S.col_letter(4), 'E')   # 状態列
        self.assertEqual(S.col_letter(10), 'K')
        self.assertEqual(S.col_letter(26), 'AA')

    def test_find_header_row(self):
        self.assertEqual(S.find_header_row(SHEET), 3)

    def test_find_header_row_absent(self):
        self.assertEqual(S.find_header_row([['a', 'b'], ['c', 'd']]), -1)

    def test_col_index(self):
        self.assertEqual(S.col_index(HEADER, 'id', 'no'), 0)
        self.assertEqual(S.col_index(HEADER, '状態'), 4)
        self.assertEqual(S.col_index(HEADER, '種別'), 2)
        self.assertEqual(S.col_index(HEADER, '存在しない列'), -1)

    def test_pad_and_tsv(self):
        self.assertEqual(len(S.pad(['a', 'b'])), S.COLS)
        self.assertEqual(S.pad(['a'] * 15), ['a'] * 11)   # 11列に切り詰め
        self.assertEqual(S.to_tsv([['a', 'b']]).count('\t'), 10)   # 11列→タブ10個

    def test_a1_range_escapes_quote(self):
        self.assertEqual(S.a1_range("Sheet1", 'A:K'), "'Sheet1'!A:K")
        self.assertEqual(S.a1_range("O'Brien", 'E5'), "'O''Brien'!E5")

    def test_status_cell_resolution(self):
        """set-status が更新するセルの特定ロジック（ID=21の状態セル=E6）"""
        hidx = S.find_header_row(SHEET)
        header = SHEET[hidx]
        id_col = S.col_index(header, 'id', 'no')
        st_col = S.col_index(header, '状態')
        hit = next(r for r in range(hidx + 1, len(SHEET))
                   if str(SHEET[r][id_col]).strip() == '21')
        cell = '{}{}'.format(S.col_letter(st_col), hit + 1)
        self.assertEqual(cell, 'E6')


if __name__ == '__main__':
    unittest.main(verbosity=2)
