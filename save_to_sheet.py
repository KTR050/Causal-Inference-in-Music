# save_to_sheet.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def save_to_sheet(spreadsheet_title, worksheet_name, data_row):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # 「研究」スプレッドシートの「アンケート集計」ワークシートを開く
    sheet = client.open(spreadsheet_title).worksheet(worksheet_name)
    sheet.append_row(data_row)
