import streamlit as st

st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

# 🔽 サイドバー（自動ページリンク）を非表示にするCSS
hide_pages_css = """
<style>
    [data-testid="stSidebarNav"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
</style>
"""
st.markdown(hide_pages_css, unsafe_allow_html=True)

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
""")

# ==== 状態管理 ====
if "register_disabled" not in st.session_state:
    st.session_state.register_disabled = False
if "registered" not in st.session_state:
    st.session_state.registered = False

with st.form("register_form"):
    gender = st.radio("性別を選んでください", ["男性", "女性"])
    age_input = st.text_input("年齢を入力してください（数字のみ）")

    try:
        age = int(age_input)
    except ValueError:
        age = None

    if age is None and age_input != "":
        st.warning("数字を入力してください")

    # ボタン押下
    submitted = st.form_submit_button(
        "登録する",
        disabled=st.session_state.register_disabled or st.session_state.registered
    )

# ==== 登録処理 ====
if submitted and not st.session_state.registered:
    # 押した瞬間に無効化
    st.session_state.register_disabled = True
    st.rerun()

# ==== 押下後の処理 ====
if st.session_state.register_disabled and not st.session_state.registered:
    try:
        gender_value = 1 if gender == "男性" else 0

        if age is None:
            raise ValueError("年齢が未入力です。")

        participant_id = get_next_id("研究", "被験者リスト")

        # Google Sheetに保存
        row = [participant_id, gender_value, age]
        save_to_sheet("研究", "被験者リスト", row)

        # 成功したら登録完了扱いに
        st.session_state.participant_info = {
            "id": participant_id,
            "gender": gender_value,
            "age": age
        }
        st.session_state.trial = 1
        st.session_state.registered = True

        st.success(f"登録完了！ あなたのIDは {participant_id} です。")
        st.page_link("pages/02_音楽選好実験.py", label="👉 実験ページへ進む", icon="🎵")

    except Exception as e:
        # エラー発生時 → 再度ボタン押下可能に戻す
        st.error(f"登録に失敗しました: {e}")
        st.session_state.register_disabled = False

elif st.session_state.registered:
    st.info("✅ 登録済みです。下のリンクから実験ページへ進んでください。")
    st.page_link("pages/02_音楽選好実験.py", label="🎵 実験ページへ進む")
