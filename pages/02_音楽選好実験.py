import os
import random
import numpy as np
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== フォルダ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [0.8, 1.0, 1.4]   # ピッチ/テンポ倍率
price_options = [25, 50, 100]
TRIALS_PER_PERSON = 10

# ==== セッション管理 ====
if "participant_info" not in st.session_state:
    st.error("⚠️ 先に登録ページで情報を入力してください。")
    st.stop()

if "trial" not in st.session_state:
    st.session_state.trial = 1

participant = st.session_state.participant_info
trial = st.session_state.trial

st.title(f"音楽選好実験（試行 {trial}/{TRIALS_PER_PERSON}）")

# ==== スプレッドシートヘッダー取得 ====
def get_sheet_header(spreadsheet_title, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_title).worksheet(worksheet_name)
    return sheet.row_values(1)

header = get_sheet_header("研究", "アンケート集計")

# ==== 1行目に従って0/1リストを作成 ====
def make_binary_row(base_info, elements_dict, header):
    row = base_info.copy()
    for col in header[len(base_info):]:
        row.append(1 if elements_dict.get(col, False) else 0)
    return row

# ==== 曲生成 ====
def generate_mix():
    key_type = random.choice(["メジャー", "マイナー"])
    base_path = os.path.join(AUDIO_FOLDER, key_type)

    def pick_file(folder):
        path = os.path.join(base_path, folder)
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".wav")]
        if not files:
            raise FileNotFoundError(f"{path} に音声ファイルがありません")
        return random.choice(files)

    bass_file = pick_file("ベース")
    chord_file = pick_file("コード")
    melody_file = pick_file("メロディ")
    drum_file = random.choice([os.path.join(AUDIO_FOLDER,"ドラム",f) for f in os.listdir(os.path.join(AUDIO_FOLDER,"ドラム")) if f.endswith(".wav")])

    y_bass, sr = librosa.load(bass_file, sr=None, mono=True)
    y_chord, _ = librosa.load(chord_file, sr=sr, mono=True)
    y_melody, _ = librosa.load(melody_file, sr=sr, mono=True)
    y_drum, _ = librosa.load(drum_file, sr=sr, mono=True)

    # 長さ合わせ
    min_len = min(len(y_bass), len(y_chord), len(y_melody), len(y_drum))
    mix = y_bass[:min_len] + y_chord[:min_len] + y_melody[:min_len] + y_drum[:min_len]
    mix = mix.astype(np.float32)

    # ランダムキー変換（ドラム以外）
    semitone_shift = random.randint(-5,5)
    try:
        mix_non_drum = y_bass[:min_len] + y_chord[:min_len] + y_melody[:min_len]
        mix_non_drum = librosa.effects.pitch_shift(mix_non_drum, sr, n_steps=semitone_shift)
        mix = mix_non_drum + y_drum[:min_len]
    except:
        pass

    mix = mix / np.max(np.abs(mix)+1e-6)
    tempo = random.choice(bpm_options)
    price = random.choice(price_options)

    return {
        "mix": mix, "sr": sr, "key_type": key_type,
        "semitone_shift": semitone_shift, "tempo": tempo, "price": price,
        "bass": os.path.basename(bass_file),
        "chord": os.path.basename(chord_file),
        "melody": os.path.basename(melody_file),
        "drum": os.path.basename(drum_file)
    }

# ==== 曲A/B生成 ====
if f"mixA_{trial}" not in st.session_state:
    st.session_state[f"mixA_{trial}"] = generate_mix()
    st.session_state[f"mixB_{trial}"] = generate_mix()

mixA_info = st.session_state[f"mixA_{trial}"]
mixB_info = st.session_state[f"mixB_{trial}"]

fileA = os.path.join(TEMP_FOLDER,f"mixA_{trial}.wav")
fileB = os.path.join(TEMP_FOLDER,f"mixB_{trial}.wav")
sf.write(fileA, mixA_info["mix"], mixA_info["sr"])
sf.write(fileB, mixB_info["mix"], mixB_info["sr"])

# ==== UI ====
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
        # 内部選好
        internal_pref_A = 1 if rankA < rankB else 0
        internal_pref_B = 1 if rankB < rankA else 0
        # 外部選好
        external_pref_A = 1 if rankA < rankExt else 0
        external_pref_B = 1 if rankB < rankExt else 0

        baseA = [participant["id"], participant["gender"], participant["age"], trial, internal_pref_A, external_pref_A]
        baseB = [participant["id"], participant["gender"], participant["age"], trial, internal_pref_B, external_pref_B]

        key_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

        def build_elements_dict(mix_info):
            prefix = "M" if mix_info["key_type"]=="メジャー" else "m"
            elements = {}
            # 仮: ベース/コード/メロディの末尾数字を使用して1-hot化
            elements[f"{prefix}ベース{mix_info['bass'][-5]}"] = True
            elements[f"{prefix}コード{mix_info['chord'][-5]}"] = True
            elements[f"{prefix}メロディ{mix_info['melody'][-5]}"] = True
            elements[f"ドラム{mix_info['drum'][-5]}"] = True
            # BPM
            bpm_int = int(mix_info["tempo"]*100)
            elements[f"BPM{bpm_int}"] = True
            # 価格
            elements[f"{mix_info['price']}円"] = True
            # キー
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
