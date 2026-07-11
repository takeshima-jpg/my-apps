#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aix-drafts フォルダの固定名ファイル重複を掃除する（夜間ジョブ）。

手作業でやっていた「固定名ファイルは最新1つだけ残し、古い同名はゴミ箱へ」を自動化する。
日付つきスナップショットや対象外の名前のファイルには一切触らない。削除は必ずゴミ箱
（trashed=true）で、完全削除はしない（30日は復元可能）。

使い方:
    python tools/drive_cleanup.py --dry-run     # 削除せず対象を表示（初週はこれで運用）
    python tools/drive_cleanup.py               # 実際にゴミ箱へ移動

初回のみブラウザ認可が必要。認証設定は tools/README.md 参照。
"""

import os
import sys
import argparse
from datetime import datetime

# Windowsコンソール(cp932)でも日本語ログを出力できるよう標準出力をUTF-8化
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print('必要ライブラリが未導入です。次を実行してください:')
    print('  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib')
    sys.exit(2)

# ── 設定 ───────────────────────────────────────────────────────
FOLDER_ID = '1dEA4ZZJi5E97Dk_MRNwG6EbBlINlMO3U'   # aix-drafts フォルダ
# token.json を sheet_update.py と共用するため、スコープはドライブ＋シートの和集合にそろえる
# （この掃除ツール自体が使うのは drive スコープのみ）
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]

# 最新1件だけ残し、古い同名はゴミ箱へ入れる対象（完全一致のみ）
TARGET_NAMES = {
    'aix-tasks.json',
    'aix_draft_latest.json',
    'aix_review_weekly.json',
    'aix_review_monthly.json',
    'aix-hitomemo.json',
    'myapps-all-backup.json',
}

HERE = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(HERE, 'credentials.json')  # OAuthクライアント（デスクトップ）
TOKEN_FILE = os.path.join(HERE, 'token.json')              # refresh_token 保存先
LOG_DIR = os.path.join(HERE, 'logs')


# ── ログ ───────────────────────────────────────────────────────
class Logger:
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        day = datetime.now().strftime('%Y-%m-%d')
        self.path = os.path.join(LOG_DIR, 'drive_cleanup_{}.log'.format(day))
        self.fh = open(self.path, 'a', encoding='utf-8')

    def log(self, msg):
        line = '{} {}'.format(datetime.now().strftime('%H:%M:%S'), msg)
        print(line)
        self.fh.write(line + '\n')

    def close(self):
        self.fh.close()


# ── 認証 ───────────────────────────────────────────────────────
def get_service():
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
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


# ── フォルダ内ファイル取得 ─────────────────────────────────────
def list_files(service):
    files = []
    page_token = None
    q = "'{}' in parents and trashed = false".format(FOLDER_ID)
    while True:
        resp = service.files().list(
            q=q,
            spaces='drive',
            fields='nextPageToken, files(id, name, modifiedTime, createdTime)',
            pageToken=page_token,
            pageSize=1000,
        ).execute()
        files.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return files


# ── メイン処理 ─────────────────────────────────────────────────
def run(dry_run):
    logger = Logger()
    mode = 'DRY-RUN（削除なし）' if dry_run else '本実行'
    logger.log('==== drive_cleanup 開始 [{}] folder={} ===='.format(mode, FOLDER_ID))
    try:
        service = get_service()
        files = list_files(service)
    except Exception as e:
        logger.log('✗ Drive接続/取得エラー: {}'.format(e))
        logger.close()
        return 2

    # 対象名ごとにグループ化（完全一致のみ。対象外・日付つきは自動的に対象外）
    groups = {}
    for f in files:
        if f['name'] in TARGET_NAMES:
            groups.setdefault(f['name'], []).append(f)

    trashed = 0
    kept = 0
    for name in sorted(groups):
        items = groups[name]
        # 新しい順（modifiedTime 降順）。無ければ createdTime。
        items.sort(key=lambda x: x.get('modifiedTime') or x.get('createdTime') or '', reverse=True)
        keep = items[0]
        kept += 1
        logger.log('◯ 残す: {} (id={} mtime={})'.format(name, keep['id'], keep.get('modifiedTime')))
        for old in items[1:]:
            if dry_run:
                logger.log('  → [DRY] ゴミ箱対象: {} (id={} mtime={})'.format(name, old['id'], old.get('modifiedTime')))
            else:
                try:
                    service.files().update(fileId=old['id'], body={'trashed': True}).execute()
                    logger.log('  → ゴミ箱へ: {} (id={} mtime={})'.format(name, old['id'], old.get('modifiedTime')))
                except Exception as e:
                    logger.log('  ✗ ゴミ箱移動失敗: {} (id={}) {}'.format(name, old['id'], e))
                    continue
            trashed += 1

    if not groups:
        logger.log('対象の固定名ファイルは見つかりませんでした。')
    verb = '対象' if dry_run else '移動'
    logger.log('---- 完了: 残した種別 {}件 / ゴミ箱{} {}件 ----'.format(kept, verb, trashed))
    logger.log('ログ: {}'.format(logger.path))
    logger.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description='aix-drafts の固定名ファイル重複を掃除（古い同名をゴミ箱へ）')
    ap.add_argument('--dry-run', action='store_true', help='削除せず対象だけ表示（初週はこれで運用）')
    args = ap.parse_args()
    return run(args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
