import os
import random
import numpy as np
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== フォルダ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ==== 実験設定 ====
bpm_options = [0.8, 1.0, 1.4]  # テンポ倍率
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

# ==== ミックス生成関数 ====
def generate_mix():
    key_type = random.choice(["メジャー", "マイナー"])
    base_path = os.path.join(AUDIO_FOLDER, key_type)

    def pick_random_file(folder):
        path = os.path.join(base_path, folder)
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".wav")]
        if not files:
            raise FileNotFoundError(f"{path} に音声ファイルがありません")
        return random.choice(files)

    # ==== ファイル選択 ====
    bass_file = pick_random_file("ベース")
    chord_file = pick_random_file("コード")
    melody_file = pick_random_file("メロディ")

    drum_folder = os.path.join(AUDIO_FOLDER, "ドラム")
    drum_file = random.choice([os.path.join(drum_folder, f) for f in os.listdir(drum_folder) if f.endswith(".wav")])

    # ==== 音声読み込み ====
    y_bass, sr = librosa.load(bass_file, sr=None, mono=True)
    y_chord, _ = librosa.load(chord_file, sr=sr, mono=True)
    y_melody, _ = librosa.load(melody_file, sr=sr, mono=True)
    y_drum, _ = librosa.load(drum_file, sr=sr, mono=True)

    # ==== 長さ合わせ ====
    min_len = min(len(y_bass), len(y_chord), len(y_melody), len(y_drum))
    y_bass, y_chord, y_melody, y_drum = (
        y_bass[:min_len],
        y_chord[:min_len],
        y_melody[:min_len],
        y_drum[:min_len],
    )

    # ==== ランダムキー変換（ドラム以外） ====
    semitone_shift = random.randint(-5, 5)
    if semitone_shift != 0:
        try:
            y_bass = librosa.effects.pitch_shift(y_bass, sr=sr, n_steps=semitone_shift)
            y_chord = librosa.effects.pitch_shift(y_chord, sr=sr, n_steps=semitone_shift)
            y_melody = librosa.effects.pitch_shift(y_melody, sr=sr, n_steps=semitone_shift)
        except Exception as e:
            st.warning(f"キー変更をスキップしました: {e}")

    # ==== 合成 ====
    mix = y_bass + y_chord + y_melody + y_drum

    # ==== テンポ変更（ピッチ維持）====
    tempo = random.choice(bpm_options)
    if tempo != 1.0 and len(mix) > 2048:
        try:
            mix = librosa.effects.time_stretch(mix, rate=tempo)
        except Exception as e:
            st.warning(f"テンポ変更をスキップしました: {e}")

    mix = mix / np.max(np.abs(mix) + 1e-6)

    return (
        mix, sr, key_type, tempo, semitone_shift,
        os.path.basename(bass_file), os.path.basename(chord_file),
        os.path.basename(melody_file), os.path.basename(drum_file)
    )

# ==== 曲A/B生成 ====
if f"mixA_{trial}" not in st.session_state:
    st.session_state[f"mixA_{trial}"] = generate_mix()
    st.session_state[f"mixB_{trial}"] = generate_mix()

mixA, srA, typeA, tempoA, keyShiftA, bassA, chordA, melodyA, drumA = st.session_state[f"mixA_{trial}"]
mixB, srB, typeB, tempoB, keyShiftB, bassB, chordB, melodyB, drumB = st.session_state[f"mixB_{trial}"]

# ==== 一時ファイル保存 ====
fileA = os.path.join(TEMP_FOLDER, f"mixA_{trial}.wav")
fileB = os.path.join(TEMP_FOLDER, f"mixB_{trial}.wav")
sf.write(fileA, mixA, srA)
sf.write(fileB, mixB, srB)

# ==== UI ====
priceA = random.choice(price_options)
priceB = random.choice(price_options)

st.markdown(f"### 曲A（{typeA}, tempo={tempoA}x, key shift={keyShiftA:+}） 価格: {priceA}円")
st.audio(fileA, format="audio/wav")

st.markdown(f"### 曲B（{typeB}, tempo={tempoB}x, key shift={keyShiftB:+}） 価格: {priceB}円")
st.audio(fileB, format="audio/wav")

st.markdown("### External Option（どちらも買わない）")

rank_options = [1, 2, 3]
rankA = st.selectbox("曲Aの順位", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("曲Bの順位", rank_options, key=f"rankB_{trial}")
rankExt = st.selectbox("どちらも買わないの順位", rank_options, key=f"rankExt_{trial}")

# ==== 保存 ====
if len({rankA, rankB, rankExt}) < 3:
    st.warning("各順位（1, 2, 3）は一度ずつ使用してください。")
else:
    if st.button("送信"):
        row = [
            participant["id"], participant["gender"], participant["age"], trial,
            bassA, chordA, melodyA, drumA, priceA, tempoA, keyShiftA, rankA,
            bassB, chordB, melodyB, drumB, priceB, tempoB, keyShiftB, rankB,
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
