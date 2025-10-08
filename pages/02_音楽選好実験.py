import os
import random
import numpy as np
import librosa
import soundfile as sf
import pyrubberband as pyrb
import streamlit as st
from scipy.signal import butter, lfilter
from save_to_sheet import save_to_sheet

# ==== フォルダ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [0.8, 1.0, 1.4]
price_options = [25, 50, 100]
TRIALS_PER_PERSON = 10

# ==== EQ設定 ====
eq_bands = ["low", "mid", "high"]
eq_values = [0.9, 1.0, 1.1]

# ==== セッション管理 ====
if "participant_info" not in st.session_state:
    st.error("⚠️ 先に登録ページで情報を入力してください。")
    st.stop()

if "trial" not in st.session_state:
    st.session_state.trial = 1

participant = st.session_state.participant_info
trial = st.session_state.trial

st.title(f"音楽選好実験（試行 {trial}/{TRIALS_PER_PERSON}）")

# ==== EQ関数 ====
def apply_eq(y, sr, gains):
    def bandpass(y, low, high):
        b, a = butter(4, [low/(sr/2), high/(sr/2)], btype='band')
        return lfilter(b, a, y)
    low = bandpass(y, 20, 250) * gains["low"]
    mid = bandpass(y, 250, 4000) * gains["mid"]
    high = bandpass(y, 4000, 12000) * gains["high"]
    mix = low + mid + high
    return mix / np.max(np.abs(mix))

# ==== トラック生成 ====
def generate_mix():
    key_type = random.choice(["メジャー", "マイナー"])
    base_path = os.path.join(AUDIO_FOLDER, key_type)

    def pick_random_file(folder):
        path = os.path.join(base_path, folder)
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".wav")]
        return random.choice(files)

    bass_file = pick_random_file("ベース")
    chord_file = pick_random_file("コード")
    melody_file = pick_random_file("メロディ")
    drum_file = random.choice([os.path.join(AUDIO_FOLDER, "ドラム", f)
                               for f in os.listdir(os.path.join(AUDIO_FOLDER, "ドラム")) if f.endswith(".wav")])

    y_bass, sr = librosa.load(bass_file, sr=None)
    y_chord, _ = librosa.load(chord_file, sr=None)
    y_melody, _ = librosa.load(melody_file, sr=None)
    y_drum, _ = librosa.load(drum_file, sr=None)

    min_len = min(len(y_bass), len(y_chord), len(y_melody), len(y_drum))
    mix = y_bass[:min_len] + y_chord[:min_len] + y_melody[:min_len] + y_drum[:min_len]

    # ランダムEQ適用
    eq_gain = {b: random.choice(eq_values) for b in eq_bands}
    mix = apply_eq(mix, sr, eq_gain)

    # テンポ変更（音程維持）
    tempo = random.choice(bpm_options)
    if tempo != 1.0:
        mix = pyrb.time_stretch(mix, sr, tempo)

    # ランダムキー変換（-5〜+5半音）
    semitone_shift = random.randint(-5, 5)
    if semitone_shift != 0:
        mix = pyrb.pitch_shift(mix, sr, semitone_shift)

    mix = mix / np.max(np.abs(mix))

    return mix, sr, key_type, tempo, eq_gain, semitone_shift, os.path.basename(bass_file), os.path.basename(chord_file), os.path.basename(melody_file), os.path.basename(drum_file)

# ==== 曲A/B生成（1試行で固定） ====
if f"mixA_{trial}" not in st.session_state:
    st.session_state[f"mixA_{trial}"] = generate_mix()
    st.session_state[f"mixB_{trial}"] = generate_mix()

mixA, srA, typeA, tempoA, eqA, keyShiftA, bassA, chordA, melodyA, drumA = st.session_state[f"mixA_{trial}"]
mixB, srB, typeB, tempoB, eqB, keyShiftB, bassB, chordB, melodyB, drumB = st.session_state[f"mixB_{trial}"]

# ==== 一時保存 ====
fileA = os.path.join(TEMP_FOLDER, f"mixA_{trial}.wav")
fileB = os.path.join(TEMP_FOLDER, f"mixB_{trial}.wav")
sf.write(fileA, mixA, srA)
sf.write(fileB, mixB, srB)

# ==== UI ====
priceA, priceB = random.choice(price_options), random.choice(price_options)
st.markdown(f"### 曲A（{typeA}, {tempoA}x, key shift {keyShiftA:+}） 価格: {priceA}円")
st.audio(fileA, format="audio/wav")

st.markdown(f"### 曲B（{typeB}, {tempoB}x, key shift {keyShiftB:+}） 価格: {priceB}円")
st.audio(fileB, format="audio/wav")

st.markdown("External Option（どちらも買わない）")

rank_options = [1, 2, 3]
rankA = st.selectbox("曲Aの順位", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("曲Bの順位", rank_options, key=f"rankB_{trial}")
rankExt = st.selectbox("どちらも買わないの順位", rank_options, key=f"rankExt_{trial}")

if len({rankA, rankB, rankExt}) < 3:
    st.warning("各順位（1, 2, 3）は一度ずつ使用してください。")
else:
    if st.button("送信"):
        row = [
            participant["id"], participant["gender"], participant["age"], trial,
            bassA, chordA, melodyA, drumA, priceA, tempoA, str(eqA), keyShiftA, rankA,
            bassB, chordB, melodyB, drumB, priceB, tempoB, str(eqB), keyShiftB, rankB,
            rankExt
        ]
        save_to_sheet("研究", "アンケート集計", row)
        st.success(f"試行 {trial} の回答を保存しました。")

        if trial < TRIALS_PER_PERSON:
            st.session_state.trial += 1
            st.rerun()
        else:
            st.balloons()
            st.success("全ての試行が完了しました！")
