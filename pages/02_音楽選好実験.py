import os
import random
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== フォルダ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [0.8, 1.2, 2]
price_options = [25,50,100]
TRIALS_PER_PERSON = 10

# ==== セッションチェック ====
if "participant_info" not in st.session_state:
    st.error("⚠️ 先に登録ページで情報を入力してください")
    st.stop()

if "trial" not in st.session_state:
    st.session_state.trial = 1

participant = st.session_state.participant_info
trial = st.session_state.trial

# ==== UI ====
st.title(f"音楽選好実験（試行 {trial}/{TRIALS_PER_PERSON}）")

files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]
fileA, fileB = random.sample(files, 2)
tempoA, tempoB = random.choice(bpm_options), random.choice(bpm_options)
priceA, priceB = random.choice(price_options), random.choice(price_options)
musicnameA, musicnameB = fileA.replace(".wav", ""), fileB.replace(".wav", "")

processed_fileA = os.path.join(TEMP_FOLDER, "processed_A.wav")
processed_fileB = os.path.join(TEMP_FOLDER, "processed_B.wav")
y, sr = librosa.load(os.path.join(AUDIO_FOLDER, fileA), sr=None)
y = librosa.effects.time_stretch(y, rate=tempoA)
sf.write(processed_fileA, y, sr)
y, sr = librosa.load(os.path.join(AUDIO_FOLDER, fileB), sr=None)
y = librosa.effects.time_stretch(y, rate=tempoB)
sf.write(processed_fileB, y, sr)

st.audio(processed_fileA, format="audio/wav")
st.audio(processed_fileB, format="audio/wav")

rank_options = [1, 2, 3]
rankA = st.selectbox("曲Aを買う", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("曲Bを買う", rank_options, key=f"rankB_{trial}")
rankExt = st.selectbox("どちらも買わない", rank_options, key=f"rankExt_{trial}")

ranks = [rankA, rankB, rankExt]
valid = len(set(ranks)) == 3

if st.button("送信"):
    if not valid:
        st.error("順位が重複しています。")
    else:
        row = [
            participant["id"], participant["gender"], participant["age"],
            trial,
            musicnameA, tempoA, priceA, rankA,
            musicnameB, tempoB, priceB, rankB,
            rankExt
        ]
        save_to_sheet("研究", "アンケート集計", row)
        st.success(f"試行 {trial}/{TRIALS_PER_PERSON} の回答を保存しました。")

        if trial < TRIALS_PER_PERSON:
            st.session_state.trial += 1
            st.rerun()
        else:
            st.balloons()
            st.success("全ての試行が完了しました！")

