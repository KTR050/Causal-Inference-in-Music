import os
import base64
import streamlit as st
import numpy as np
import soundfile as sf
import librosa
import tempfile
import random
from save_to_sheet import save_to_sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ===== Streamlit設定 =====
st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

# ==== サイドバー・ツールバー非表示 ====
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
    st.error("Google認証情報（GOOGLE_CREDENTIALS_B64）が設定されていません。")
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

# ==== ページ制御 ====
if "page" not in st.session_state:
    st.session_state.page = "home"


# ===== ページ1: ホーム =====
if st.session_state.page == "home":
    st.title("🎵 音楽選好実験へようこそ")

    st.markdown("""
    このアプリでは音楽の聴取実験を行います。  

    1️⃣ まず「被験者登録」で性別と年齢を入力してください。  
    2️⃣ その後、「音楽選好実験」に進みます。  
    """)

    if st.button("🧑‍💼 被験者登録へ進む"):
        st.session_state.page = "register"
        st.rerun()


# ===== ページ2: 被験者登録 =====
elif st.session_state.page == "register":
    st.title("🧑‍💼 被験者登録")

    if "register_disabled" not in st.session_state:
        st.session_state.register_disabled = False

    with st.form("register_form"):
        gender = st.radio("性別を選んでください", ["男性", "女性"])
        age_input = st.text_input("年齢を入力してください（数字のみ）")

        try:
            age = int(age_input)
        except ValueError:
            age = None

        submitted = st.form_submit_button("登録する", disabled=st.session_state.register_disabled)

    if submitted:
        st.session_state.register_disabled = True
        if age is None:
            st.warning("年齢は数字で入力してください。")
            st.session_state.register_disabled = False
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
                st.toast("🎶 音楽選好実験へ移動します...", icon="➡️")

                st.session_state.page = "experiment"
                st.rerun()

            except Exception as e:
                st.error(f"登録中にエラーが発生しました: {e}")
                st.session_state.register_disabled = False


# ===== ページ3: 音楽選好実験 =====
elif st.session_state.page == "experiment":
    st.title("🎶 音楽選好実験")

    # ===== データセット設定 =====
    base_path = "データセット"
    key_types = ["メジャー", "マイナー"]
    parts = ["ベース", "コード", "メロディ", "ドラム"]

    # ==== ミックス生成 ====
    def generate_mix():
    key_type = random.choice(["メジャー", "マイナー"])
    sources, names = [], []

    # メジャー/マイナー用パート
    tonal_parts = ["ベース", "コード", "メロディ"]
    for part in tonal_parts:
        folder = os.path.join(base_path, key_type, part)
        if not os.path.exists(folder):
            raise FileNotFoundError(f"フォルダが見つかりません: {folder}")

        files = [f for f in os.listdir(folder) if f.endswith(".wav")]
        if not files:
            raise FileNotFoundError(f"音声ファイルが存在しません: {folder}")

        choice = random.choice(files)
        y, sr = librosa.load(os.path.join(folder, choice), sr=None)
        sources.append(y)
        names.append(f"{key_type}_{part}_{choice}")

    # ドラムはトップ階層から
    drum_folder = os.path.join(base_path, "ドラム")
    if not os.path.exists(drum_folder):
        raise FileNotFoundError(f"ドラムフォルダが見つかりません: {drum_folder}")

    drum_files = [f for f in os.listdir(drum_folder) if f.endswith(".wav")]
    if not drum_files:
        raise FileNotFoundError(f"ドラム音声ファイルが存在しません: {drum_folder}")

    drum_choice = random.choice(drum_files)
    y, sr = librosa.load(os.path.join(drum_folder, drum_choice), sr=None)
    sources.append(y)
    names.append(f"ドラム_{drum_choice}")

    # ===== 長さを合わせてミックス =====
    min_len = min(len(x) for x in sources)
    sources = [x[:min_len] for x in sources]

    mix = np.sum(sources, axis=0)
    mix /= np.max(np.abs(mix)) + 1e-6

    return mix, sr, key_type, names


    # ==== 曲生成 ====
    if f"mixA_{st.session_state.trial}" not in st.session_state:
        st.session_state[f"mixA_{st.session_state.trial}"] = generate_mix()
        st.session_state[f"mixB_{st.session_state.trial}"] = generate_mix()

    mixA, srA, keyA, namesA = st.session_state[f"mixA_{st.session_state.trial}"]
    mixB, srB, keyB, namesB = st.session_state[f"mixB_{st.session_state.trial}"]

    # ==== 一時保存 ====
    tmpA = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmpB = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(tmpA.name, mixA, srA)
    sf.write(tmpB.name, mixB, srB)

    # ==== 表示 ====
    st.subheader(f"試行 {st.session_state.trial}/10")
    st.write("以下の2曲を聴いて、より好ましい方を選んでください。")

    col1, col2 = st.columns(2)
    with col1:
        st.audio(tmpA.name, format="audio/wav")
        st.write("🎵 曲A")
    with col2:
        st.audio(tmpB.name, format="audio/wav")
        st.write("🎵 曲B")

    choice = st.radio("どちらを好みますか？", ["曲A", "曲B", "どちらも買わない"], horizontal=True)
    price_choice = st.radio("購入価格を選んでください：", ["100円", "50円"], horizontal=True)

    if st.button("次へ"):
        pid = st.session_state.participant_info["id"]
        gender = st.session_state.participant_info["gender"]
        age = st.session_state.participant_info["age"]
        round_num = st.session_state.trial

        internal_pref = 1 if choice == "曲A" else (0 if choice == "曲B" else "")
        external_pref = 1 if choice != "どちらも買わない" else 0

        # ==== Cを除くカラム ====
        columns = [
            "Mベース1","Mベース2","Mベース3",
            "mベース1","mベース2","mベース3",
            "Mコード1","Mコード2","Mコード3",
            "mコード1","mコード2","mコード3",
            "Mメロディ1","Mメロディ2","Mメロディ3","Mメロディ4",
            "mメロディ1","mメロディ2","mメロディ3","mメロディ4",
            "ドラム1","ドラム2","ドラム3",
            "BPM100","BPM140","100円","50円",
            "A","A#","B","C#","D","D#","E","F","F#","G","G#"
        ]

        # ==== ランダム0/1リスト ====
        rowA = [pid, gender, age, round_num, internal_pref, external_pref] + [random.randint(0, 1) for _ in range(len(columns))]
        rowB = [pid, gender, age, round_num, internal_pref, external_pref] + [random.randint(0, 1) for _ in range(len(columns))]

        save_to_sheet("研究", "選好データ", rowA)
        save_to_sheet("研究", "選好データ", rowB)

        st.session_state.trial += 1

        if st.session_state.trial > 10:
            st.success("🎉 実験完了！ご協力ありがとうございました！")
        else:
            st.rerun()

