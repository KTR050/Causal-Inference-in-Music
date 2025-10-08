# save_to_sheet.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ===== Google Sheets 接続 =====
def connect_sheet(spreadsheet_title, worksheet_name):
    """指定されたスプレッドシートとワークシートを開く"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_title).worksheet(worksheet_name)
    return sheet


# ===== ID自動付与 =====
def get_next_id(spreadsheet_title, worksheet_name):
    """
    スプレッドシート内の次のIDを取得
    - 1行目はヘッダー想定
    - n行目に書くとき ID = n - 1
    """
    sheet = connect_sheet(spreadsheet_title, worksheet_name)
    records = sheet.get_all_values()
    n_rows = len(records) + 1  # 次の行番号
    next_id = n_rows - 1       # ID = n - 1
    return next_id


# ===== データ追加 =====
def save_to_sheet(spreadsheet_title, worksheet_name, data_row):
    """
    指定ワークシートに1行追加
    data_row はリスト形式
    """
    sheet = connect_sheet(spreadsheet_title, worksheet_name)
    sheet.append_row(data_row)
