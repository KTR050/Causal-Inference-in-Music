import streamlit as st
import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from save_to_sheet import save_to_sheet

# ==== ページ設定 ====
st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

# ==== カスタムCSS：サイドバー完全非表示 ====
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stToolbar"] {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==== Google認証 ====
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))
else:
    st.error("GOOGLE_CREDENTIALS_B64 が設定されていません。")
    st.stop()

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


# ==== ページ遷移制御 ====
if "page" not in st.session_state:
    st.session_state.page = "home"  # 初期ページをapp（ホーム）に設定

# ==== ページ：トップ ====
if st.session_state.page == "home":
    st.title("🎵 音楽選好実験へようこそ")

    st.markdown("""
    このアプリでは、音楽の聴取実験を行います。  

    1️⃣ まず「被験者登録」で性別と年齢を入力してください。  
    2️⃣ その後、「音楽選好実験」に進みます。  
    """)

    if st.button("🧑‍💼 被験者登録へ進む"):
        st.session_state.page = "register"
        st.rerun()


# ==== ページ：被験者登録 ====
elif st.session_state.page == "register":
    st.title("🧑‍💼 被験者登録")

    st.markdown("以下の情報を入力してください。登録後に自動でIDが割り振られます。")

    with st.form("register_form"):
        gender = st.radio("性別を選んでください", ["男性", "女性"])
        age_input = st.text_input("年齢を入力してください（数字のみ）")
        try:
            age = int(age_input)
        except ValueError:
            age = None

        submitted = st.form_submit_button("登録する", disabled=st.session_state.get("registering", False))

    if submitted:
        st.session_state.registering = True  # ボタン再押下防止
        if age is None:
            st.warning("年齢は数字で入力してください。")
            st.session_state.registering = False
        else:
            try:
                gender_value = 1 if gender == "男性" else 0
                participant_id = get_next_id("研究", "被験者リスト")

                row = [participant_id, gender_value, age]
                save_to_sheet("研究", "被験者リスト", row)

                st.session_state.participant_info = {
                    "id": participant_id,
                    "gender": gender_value,
                    "age": age
                }
                st.session_state.trial = 1

                st.success(f"登録完了！ あなたのIDは {participant_id} です。")
                if st.button("🎵 音楽選好実験へ進む"):
                    st.session_state.page = "experiment"
                    st.rerun()
            except Exception as e:
                st.error(f"登録中にエラーが発生しました: {e}")
                st.session_state.registering = False

# ==== ページ：音楽選好実験 ====
elif st.session_state.page == "experiment":
    st.title("🎶 音楽選好実験")

    st.write("（ここに音楽提示や順位付けのロジックを入れます）")

    if st.button("🏠 ホームへ戻る"):
        st.session_state.page = "home"
        st.rerun()
