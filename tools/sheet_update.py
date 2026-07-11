#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project OS のスプレッドシートを直接更新する（状態変更・行追加）。

    python tools/sheet_update.py <spreadsheetId> --get                 # 現状をTSVで表示
    python tools/sheet_update.py <spreadsheetId> --set-status <ID> 完了 # 状態列を更新
    python tools/sheet_update.py <spreadsheetId> --append-tsv <file>    # 行追加（TSV）
    python tools/sheet_update.py <spreadsheetId> --backup               # 全値をtools/logs/へ退避
    （対象タブは既定で先頭シート。 --gid <n> / --sheet-name <名> で指定可）

実運用はコマンド直叩きではなく、Claude Codeが自然言語の依頼を解釈して
「--get → 変更差分を提示 → 承認 → 書き込み」の流れで使う。

書き込みルール【厳守・docs/claude-code-sheets-integration-spec.md】:
  1. 書き込み前に必ず --backup で退避（本ツールは書き込み系で自動退避もする）→ 差分提示 → 所有者OK
  2. 行削除はしない（状態変更・行追加のみ）
  3. 11列構成と日付形式を崩さない
  4. 新規行IDはシートの採番規則（テーマ番号×10＋連番）に従う（読めなければ所有者に確認）
  5. 書き込み後 --get で結果を確認し、Project OSで「⟳ シートから直接取り込み」を押すよう報告

認証は drive_cleanup.py と共用（tools/credentials.json / tools/token.json）。
スコープは drive ＋ spreadsheets。設定手順は tools/README.md 参照。
"""

import os
import sys
import argparse
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass

# googleライブラリは get_service() 内で遅延importする
# （純粋ヘルパーのユニットテストをライブラリ無しでも実行できるようにするため）

# drive_cleanup.py と同じ token.json を共用するため、スコープはドライブ＋シートの和集合にする
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]
COLS = 11  # A:K = ID/テーマ/種別/期日/状態/イベント/担当/対象/施策/ゴール/結果

HERE = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(HERE, 'credentials.json')
TOKEN_FILE = os.path.join(HERE, 'token.json')
LOG_DIR = os.path.join(HERE, 'logs')

# ヘッダー行の判定シグナル（project-os の isHeaderRow と同じ考え方）
HEADER_SIGNALS = ['id', '期日', '状態', 'イベント', '種別']


# ── 認証 ───────────────────────────────────────────────────────
def get_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        print('必要ライブラリが未導入です。次を実行してください:')
        print('  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib')
        sys.exit(2)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print('OAuthクライアントが未設定です: {} を置いてください。'.format(CREDENTIALS_FILE))
                print('作成手順は tools/README.md 参照。')
                sys.exit(2)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)


# ── シート解決 ─────────────────────────────────────────────────
def resolve_sheet_title(service, spreadsheet_id, gid=None, sheet_name=None):
    meta = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields='sheets(properties(sheetId,title,index))').execute()
    sheets = meta.get('sheets', [])
    if not sheets:
        raise RuntimeError('シートが1枚もありません。')
    if sheet_name:
        for s in sheets:
            if s['properties']['title'] == sheet_name:
                return sheet_name
        raise RuntimeError('シート名「{}」が見つかりません。'.format(sheet_name))
    if gid is not None:
        for s in sheets:
            if str(s['properties']['sheetId']) == str(gid):
                return s['properties']['title']
        raise RuntimeError('gid={} のシートが見つかりません。'.format(gid))
    # 既定：先頭（index=0）
    sheets.sort(key=lambda s: s['properties'].get('index', 0))
    return sheets[0]['properties']['title']


def a1_range(title, rng):
    return "'{}'!{}".format(title.replace("'", "''"), rng)


def get_values(service, spreadsheet_id, title):
    resp = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=a1_range(title, 'A:K'),
        majorDimension='ROWS',
        valueRenderOption='FORMATTED_VALUE').execute()
    return resp.get('values', [])


def pad(row, n=COLS):
    r = list(row[:n])
    while len(r) < n:
        r.append('')
    return r


def to_tsv(rows):
    return '\n'.join('\t'.join(pad(r)) for r in rows)


def norm_h(s):
    return ''.join(str(s or '').split()).lower()


def find_header_row(rows):
    """ヘッダー行のインデックスを返す（見つからなければ -1）。"""
    for i, row in enumerate(rows):
        norms = [norm_h(c) for c in row]
        hit = sum(1 for sig in HEADER_SIGNALS
                  if any(norm_h(sig) == n or norm_h(sig) in n for n in norms if n))
        if hit >= 3:
            return i
    return -1


def col_index(header_row, *cands):
    """ヘッダー行から、候補名に一致する列インデックスを返す（見つからなければ -1）。"""
    norms = [norm_h(c) for c in header_row]
    for cand in cands:
        nc = norm_h(cand)
        for i, n in enumerate(norms):
            if n == nc or nc in n or (n and n in nc):
                return i
    return -1


def col_letter(idx):
    """0始まりの列インデックス → A1の列文字。"""
    s = ''
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


# ── バックアップ ───────────────────────────────────────────────
def backup(service, spreadsheet_id, title, rows=None):
    os.makedirs(LOG_DIR, exist_ok=True)
    if rows is None:
        rows = get_values(service, spreadsheet_id, title)
    stamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    path = os.path.join(LOG_DIR, 'sheet_{}_{}.tsv'.format(spreadsheet_id[:12], stamp))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('# spreadsheetId={} sheet={} savedAt={}\n'.format(spreadsheet_id, title, stamp))
        f.write(to_tsv(rows))
        f.write('\n')
    print('退避: {}'.format(path))
    return path


# ── 操作 ───────────────────────────────────────────────────────
def cmd_get(service, spreadsheet_id, title):
    rows = get_values(service, spreadsheet_id, title)
    print('# {} / シート「{}」 {}行'.format(spreadsheet_id, title, len(rows)))
    print(to_tsv(rows))
    return 0


def cmd_set_status(service, spreadsheet_id, title, target_id, new_status):
    rows = get_values(service, spreadsheet_id, title)
    hidx = find_header_row(rows)
    if hidx == -1:
        print('✗ ヘッダー行（ID/種別/期日/状態/イベント）が見つかりません。')
        return 1
    header = rows[hidx]
    id_col = col_index(header, 'id', 'no')
    st_col = col_index(header, '状態')
    if id_col == -1 or st_col == -1:
        print('✗ ID列または状態列を特定できません。')
        return 1

    hit = None
    for r in range(hidx + 1, len(rows)):
        cells = rows[r]
        if id_col < len(cells) and str(cells[id_col]).strip() == str(target_id).strip():
            hit = r
            break
    if hit is None:
        print('✗ ID={} の行が見つかりません。'.format(target_id))
        return 1

    old = rows[hit][st_col] if st_col < len(rows[hit]) else ''
    # 書き込み前に必ず退避（ルール1）
    backup(service, spreadsheet_id, title, rows)
    cell = a1_range(title, '{}{}'.format(col_letter(st_col), hit + 1))
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=cell,
        valueInputOption='USER_ENTERED',
        body={'values': [[new_status]]}).execute()
    print('✓ ID={}: 状態「{}」→「{}」（{}）'.format(target_id, old, new_status, cell))
    print('  Project OSで「⟳ シートから直接取り込み」を押して反映してください。')
    return 0


def cmd_append_tsv(service, spreadsheet_id, title, tsv_path):
    if not os.path.exists(tsv_path):
        print('✗ ファイルが見つかりません: {}'.format(tsv_path))
        return 2
    with open(tsv_path, 'r', encoding='utf-8') as f:
        new_rows = [pad(line.rstrip('\n').split('\t')) for line in f if line.strip()]
    if not new_rows:
        print('✗ 追加する行がありません。')
        return 1

    # 書き込み前に必ず退避（ルール1）
    backup(service, spreadsheet_id, title)
    print('追加する {} 行:'.format(len(new_rows)))
    for r in new_rows:
        print('  ' + '\t'.join(r))
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=a1_range(title, 'A:K'),
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': new_rows}).execute()
    print('✓ {} 行を追加しました。'.format(len(new_rows)))
    print('  Project OSで「⟳ シートから直接取り込み」を押して反映してください。')
    return 0


def main():
    ap = argparse.ArgumentParser(description='Project OS スプレッドシートの状態変更・行追加')
    ap.add_argument('spreadsheet_id')
    ap.add_argument('--gid', type=int, default=None, help='対象タブのgid（未指定は先頭シート）')
    ap.add_argument('--sheet-name', default=None, help='対象タブのシート名')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--get', action='store_true', help='現状をTSVで表示')
    g.add_argument('--set-status', nargs=2, metavar=('ID', '状態'), help='状態列を更新')
    g.add_argument('--append-tsv', metavar='FILE', help='TSVファイルの行を追加')
    g.add_argument('--backup', action='store_true', help='全値をtools/logs/へ退避')
    args = ap.parse_args()

    try:
        service = get_service()
        title = resolve_sheet_title(service, args.spreadsheet_id, args.gid, args.sheet_name)
    except Exception as e:
        print('✗ 接続/シート解決エラー: {}'.format(e))
        return 2

    try:
        if args.get:
            return cmd_get(service, args.spreadsheet_id, title)
        if args.backup:
            backup(service, args.spreadsheet_id, title)
            return 0
        if args.set_status:
            return cmd_set_status(service, args.spreadsheet_id, title, args.set_status[0], args.set_status[1])
        if args.append_tsv:
            return cmd_append_tsv(service, args.spreadsheet_id, title, args.append_tsv)
    except Exception as e:
        print('✗ 実行エラー: {}'.format(e))
        return 2


if __name__ == '__main__':
    sys.exit(main())
