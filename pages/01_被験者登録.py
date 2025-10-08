import os
import base64
import streamlit as st
from save_to_sheet import save_to_sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== Google認証 ====
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))
else:
    raise FileNotFoundError("GOOGLE_CREDENTIALS_B64 が設定されていません。")

# ==== ID取得関数 ====
def get_next_id(spreadsheet_title, worksheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_title).worksheet(worksheet_name)
    rows = len(sheet.get_all_values())
    return rows  # n行目 → id = n-1

# ==== UI ====
st.title("🧑‍💼 被験者登録")

st.markdown("""
以下の情報を入力してください。
登録後に自動でIDが割り振られます。
""")

with st.form("register_form"):
    gender = st.radio("性別を選んでください", ["男性", "女性"])
    age = st.number_input("年齢を入力してください", min_value=10, max_value=100, step=1)
    submitted = st.form_submit_button("登録する")

if submitted:
    gender_value = 1 if gender == "男性" else 0
    participant_id = get_next_id("研究", "被験者リスト")

    # 保存
    row = [participant_id, gender_value, age]
    save_to_sheet("研究", "被験者リスト", row)

    # セッション保存
    st.session_state.participant_info = {
        "id": participant_id,
        "gender": gender_value,
        "age": age
    }
    st.session_state.trial = 1

    st.success(f"登録完了！ あなたのIDは {participant_id} です。")

    st.page_link("pages/02_音楽選好実験.py", label="👉 実験ページへ進む", icon="🎵")
