import os
import base64
import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import random
from save_to_sheet import save_to_sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ===== Streamlit設定 =====
st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

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
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_title).worksheet(worksheet_name)
    rows = len(sheet.get_all_values())
    return rows

# ==== ページ制御 ====
if "page" not in st.session_state:
    st.session_state.page = "home"

# ==== ホームページ ====
if st.session_state.page == "home":
    st.title("🎵 音楽選好実験へようこそ")
    st.markdown("""
    このアプリでは音楽の聴取実験を行います。  

    1️⃣ 「被験者登録」で性別と年齢を入力してください。  
    2️⃣ 登録後に「音楽選好実験」が始まります。
    """)
    if st.button("🧑‍💼 被験者登録へ進む"):
        st.session_state.page = "register"
        st.rerun()

# ==== 被験者登録ページ ====
elif st.session_state.page == "register":
    st.title("🧑‍💼 被験者登録")
    if "registering" not in st.session_state:
        st.session_state.registering = False

    with st.form("register_form"):
        gender = st.radio("性別を選んでください", ["男性", "女性"])
        age_input = st.text_input("年齢を入力してください（数字のみ）")
        submitted = st.form_submit_button("登録する", disabled=st.session_state.registering)

    if submitted:
        st.session_state.registering = True
        try:
            age = int(age_input)
            gender_value = 1 if gender == "男性" else 0
            participant_id = get_next_id("研究", "被験者リスト")
            row = [participant_id, gender_value, age]
            save_to_sheet("研究", "被験者リスト", row)

            st.session_state.participant_info = {"id": participant_id, "gender": gender_value, "age": age}
            st.session_state.trial = 1

            st.success(f"登録完了！ あなたのIDは {participant_id} です。")
            st.session_state.registering = False
            st.session_state.page = "experiment"
            st.rerun()
        except ValueError:
            st.warning("年齢は数字で入力してください。")
            st.session_state.registering = False
        except Exception as e:
            st.error(f"登録中にエラーが発生しました: {e}")
            st.session_state.registering = False

# ==== 音楽選好実験ページ ====
elif st.session_state.page == "experiment":
    AUDIO_FOLDER = "データセット"
    TEMP_FOLDER = "temp_audio"
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    bpm_options = [0.8, 1.0, 1.2]
    price_options = [25, 50, 100]
    TRIALS_PER_PERSON = 10

    if "participant_info" not in st.session_state:
        st.error("⚠️ 先に登録ページで情報を入力してください。")
        if st.button("🧑‍💼 被験者登録へ進む"):
            st.session_state.page = "register"
            st.rerun()
        st.stop()

    if "trial" not in st.session_state:
        st.session_state.trial = 1

    participant = st.session_state.participant_info
    trial = st.session_state.trial
    st.title(f"音楽選好実験（試行 {trial}/{TRIALS_PER_PERSON}）")

    # スプレッドシートヘッダー取得
    def get_sheet_header(spreadsheet_title, worksheet_name):
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(spreadsheet_title).worksheet(worksheet_name)
        return sheet.row_values(1)

    header = get_sheet_header("研究", "アンケート集計")

    # 0/1リスト作成
    def make_binary_row(base_info, elements_dict, header):
        row = base_info.copy()
        for col in header[len(base_info):]:
            row.append(1 if elements_dict.get(col, False) else 0)
        return row

    # 曲生成
    def generate_mix():
        key_type = random.choice(["メジャー", "マイナー"])
        base_path = os.path.join(AUDIO_FOLDER, key_type)

    def pick_file(folder):
        path = os.path.join(base_path, folder)
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".wav")]
        if not files:
            raise FileNotFoundError(f"{path} に音声ファイルがありません")
        return random.choice(files)

    # 1. ランダムに音源を選ぶ
    bass_file = pick_file("ベース")
    chord_file = pick_file("コード")
    melody_file = pick_file("メロディ")
    drum_file = random.choice([os.path.join(AUDIO_FOLDER, "ドラム", f)
                               for f in os.listdir(os.path.join(AUDIO_FOLDER, "ドラム"))
                               if f.endswith(".wav")])

    # 2. 音源読み込み
    y_bass, sr = librosa.load(bass_file, sr=None, mono=True)
    y_chord, _ = librosa.load(chord_file, sr=sr, mono=True)
    y_melody, _ = librosa.load(melody_file, sr=sr, mono=True)
    y_drum, _ = librosa.load(drum_file, sr=sr, mono=True)

    # 3. ランダムキー決定
    semitone_shift = random.randint(-6, 5)

    # 4. ベース/コード/メロディにキー変更
    y_bass = librosa.effects.pitch_shift(np.array(y_bass, dtype=np.float32), sr, n_steps=semitone_shift)
    y_chord = librosa.effects.pitch_shift(np.array(y_chord, dtype=np.float32), sr, n_steps=semitone_shift)
    y_melody = librosa.effects.pitch_shift(np.array(y_melody, dtype=np.float32), sr, n_steps=semitone_shift)
    # ドラムはキー変更なし

    # 5. 長さ合わせて合成（まだBPM変更前）
    min_len = min(len(y_bass), len(y_chord), len(y_melody), len(y_drum))
    mix = y_bass[:min_len] + y_chord[:min_len] + y_melody[:min_len] + y_drum[:min_len]

    # 6. ランダムBPM倍率
    tempo = random.choice(bpm_options)

    # 7. 合成後の音声をBPM倍率で伸縮
    final_mix = librosa.effects.time_stretch(mix, tempo)
    
    # 8. 正規化
    final_mix = final_mix / (np.max(np.abs(final_mix)) + 1e-6)

    # 9. ランダム価格
    price = random.choice(price_options)

    return {
        "mix": final_mix,
        "sr": sr,
        "key_type": key_type,
        "semitone_shift": semitone_shift,
        "tempo": tempo,
        "price": price,
        "bass": os.path.basename(bass_file),
        "chord": os.path.basename(chord_file),
        "melody": os.path.basename(melody_file),
        "drum": os.path.basename(drum_file)
    }


    # 曲A/B生成
    if f"mixA_{trial}" not in st.session_state:
        st.session_state[f"mixA_{trial}"] = generate_mix()
        st.session_state[f"mixB_{trial}"] = generate_mix()

    mixA_info = st.session_state[f"mixA_{trial}"]
    mixB_info = st.session_state[f"mixB_{trial}"]

    fileA = os.path.join(TEMP_FOLDER,f"mixA_{trial}.wav")
    fileB = os.path.join(TEMP_FOLDER,f"mixB_{trial}.wav")
    sf.write(fileA, mixA_info["mix"], mixA_info["sr"])
    sf.write(fileB, mixB_info["mix"], mixB_info["sr"])

    # UI表示
    st.markdown(f"### 曲A 価格: {mixA_info['price']}円")
    st.audio(fileA, format="audio/wav")
    st.markdown(f"### 曲B 価格: {mixB_info['price']}円")
    st.audio(fileB, format="audio/wav")
    st.markdown("External Option（どちらも買わない）")

    rank_options = [1,2,3]
    rankA = st.selectbox("曲Aの順位", rank_options, key=f"rankA_{trial}")
    rankB = st.selectbox("曲Bの順位", rank_options, key=f"rankB_{trial}")
    rankExt = st.selectbox("どちらも買わない順位", rank_options, key=f"rankExt_{trial}")

    if len({rankA, rankB, rankExt}) < 3:
        st.warning("順位（1〜3）はそれぞれ1回ずつ使用してください。")
    else:
        if st.button("送信"):
            internal_pref_A = 1 if rankA < rankB else 0
            internal_pref_B = 1 if rankB < rankA else 0
            external_pref_A = 1 if rankA < rankExt else 0
            external_pref_B = 1 if rankB < rankExt else 0

            baseA = [participant["id"], participant["gender"], participant["age"], trial, internal_pref_A, external_pref_A]
            baseB = [participant["id"], participant["gender"], participant["age"], trial, internal_pref_B, external_pref_B]

            key_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
            def build_elements_dict(mix_info):
                prefix = "M" if mix_info["key_type"]=="メジャー" else "m"
                elements = {}
                elements[f"{prefix}ベース{mix_info['bass'][-5]}"] = True
                elements[f"{prefix}コード{mix_info['chord'][-5]}"] = True
                elements[f"{prefix}メロディ{mix_info['melody'][-5]}"] = True
                elements[f"ドラム{mix_info['drum'][-5]}"] = True
                bpm_int = int(mix_info["tempo"]*100)
                elements[f"BPM{bpm_int}"] = True
                elements[f"{mix_info['price']}円"] = True
                shifted_index = (key_names.index("C")+mix_info["semitone_shift"])%12
                elements[key_names[shifted_index]] = True
                return elements

            elementsA = build_elements_dict(mixA_info)
            elementsB = build_elements_dict(mixB_info)

            rowA = make_binary_row(baseA, elementsA, header)
            rowB = make_binary_row(baseB, elementsB, header)

            save_to_sheet("研究","アンケート集計",rowA)
            save_to_sheet("研究","アンケート集計",rowB)

            st.success(f"試行 {trial} の回答を保存しました。")
            if trial < TRIALS_PER_PERSON:
                st.session_state.trial += 1
                st.rerun()
            else:
                st.balloons()
                st.success("全ての試行が完了しました！")



