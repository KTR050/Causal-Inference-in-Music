import os
import random
import numpy as np
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== 設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [1.0, 1.4]  # BPM100, BPM140
price_options = [50, 100]
keys = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
TRIALS_PER_PERSON = 10

# ==== セッションチェック ====
if "participant_info" not in st.session_state:
    st.error("⚠️ 先に登録ページで情報を入力してください。")
    st.stop()

if "trial" not in st.session_state:
    st.session_state.trial = 1

participant = st.session_state.participant_info
trial = st.session_state.trial

st.title(f"音楽選好実験（試行 {trial}/{TRIALS_PER_PERSON}）")

# ==== 楽曲生成関数 ====
def generate_mix():
    key_type = random.choice(["メジャー", "マイナー"])
    base_path = os.path.join(AUDIO_FOLDER, key_type)

    def pick_random_file(folder):
        path = os.path.join(base_path, folder)
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".wav")]
        if not files:
            raise FileNotFoundError(f"{path} に音声ファイルがありません")
        return random.choice(files)

    bass_file = pick_random_file("ベース")
    chord_file = pick_random_file("コード")
    melody_file = pick_random_file("メロディ")
    drum_folder = os.path.join(AUDIO_FOLDER, "ドラム")
    drum_file = random.choice([os.path.join(drum_folder, f) for f in os.listdir(drum_folder) if f.endswith(".wav")])

    # ==== ロード（モノラル化）====
    y_bass, sr = librosa.load(bass_file, sr=None, mono=True)
    y_chord, _ = librosa.load(chord_file, sr=sr, mono=True)
    y_melody, _ = librosa.load(melody_file, sr=sr, mono=True)
    y_drum, _ = librosa.load(drum_file, sr=sr, mono=True)

    # ==== 長さ揃え ====
    min_len = min(len(y_bass), len(y_chord), len(y_melody), len(y_drum))
    y_bass, y_chord, y_melody, y_drum = [y[:min_len] for y in [y_bass, y_chord, y_melody, y_drum]]

    # ==== キー変換（ドラム以外）====
    semitone_shift = random.randint(-5, 5)
    if semitone_shift != 0:
        try:
            y_bass = librosa.effects.pitch_shift(y_bass, sr=sr, n_steps=semitone_shift)
            y_chord = librosa.effects.pitch_shift(y_chord, sr=sr, n_steps=semitone_shift)
            y_melody = librosa.effects.pitch_shift(y_melody, sr=sr, n_steps=semitone_shift)
        except Exception as e:
            st.warning(f"キー変更をスキップしました: {e}")

    mix = y_bass + y_chord + y_melody + y_drum
    mix = mix / np.max(np.abs(mix) + 1e-6)

    tempo = random.choice(bpm_options)
    return (
        mix, sr, key_type, tempo, semitone_shift,
        os.path.basename(bass_file), os.path.basename(chord_file),
        os.path.basename(melody_file), os.path.basename(drum_file)
    )

# ==== 曲A/B生成 ====
if f"mixA_{trial}" not in st.session_state:
    st.session_state[f"mixA_{trial}"] = generate_mix()
    st.session_state[f"mixB_{trial}"] = generate_mix()
    st.session_state[f"priceA_{trial}"] = random.choice(price_options)
    st.session_state[f"priceB_{trial}"] = random.choice(price_options)

mixA, srA, typeA, tempoA, keyShiftA, bassA, chordA, melodyA, drumA = st.session_state[f"mixA_{trial}"]
mixB, srB, typeB, tempoB, keyShiftB, bassB, chordB, melodyB, drumB = st.session_state[f"mixB_{trial}"]
priceA, priceB = st.session_state[f"priceA_{trial}"], st.session_state[f"priceB_{trial}"]

fileA = os.path.join(TEMP_FOLDER, f"mixA_{trial}.wav")
fileB = os.path.join(TEMP_FOLDER, f"mixB_{trial}.wav")
sf.write(fileA, mixA, srA)
sf.write(fileB, mixB, srB)

# ==== UI表示 ====
st.markdown(f"### 曲A（価格: {priceA}円）")
st.audio(fileA, format="audio/wav")
st.markdown(f"### 曲B（価格: {priceB}円）")
st.audio(fileB, format="audio/wav")
st.markdown("### External Option（どちらも買わない）")

rank_options = [1, 2, 3]
rankA = st.selectbox("曲Aの順位", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("曲Bの順位", rank_options, key=f"rankB_{trial}")
rankExt = st.selectbox("どちらも買わないの順位", rank_options, key=f"rankExt_{trial}")

# ==== データ保存 ====
if st.button("送信"):
    if len({rankA, rankB, rankExt}) < 3:
        st.error("順位が重複しています。全て異なる順位を選んでください。")
        st.stop()

    # === ワンホット関数 ===
    def one_hot_file(name, prefix, max_num):
        base = {f"{prefix}{i}": 0 for i in range(1, max_num + 1)}
        for i in range(1, max_num + 1):
            if str(i) in name:
                base[f"{prefix}{i}"] = 1
        return base

    def one_hot_key(semitone_shift):
        base = {k: 0 for k in keys}
        index_C = keys.index("C")
        shifted_index = (index_C + semitone_shift) % 12
        base[keys[shifted_index]] = 1
        return base

    def one_hot_bpm(tempo):
        return {"BPM100": 1 if tempo == 1.0 else 0, "BPM140": 1 if tempo == 1.4 else 0}

    def one_hot_price(price):
        return {"100円": 1 if price == 100 else 0, "50円": 1 if price == 50 else 0}

    def build_row(mix_type, bass, chord, melody, drum, tempo, price, keyShift):
        prefix = "M" if mix_type == "メジャー" else "m"
        row = {}
        row.update(one_hot_file(bass, f"{prefix}ベース", 3))
        row.update(one_hot_file(chord, f"{prefix}コード", 3))
        row.update(one_hot_file(melody, f"{prefix}メロディ", 4))
        row.update(one_hot_file(drum, "ドラム", 3))
        row.update(one_hot_bpm(tempo))
        row.update(one_hot_price(price))
        row.update(one_hot_key(keyShift))
        return row

    vecA = build_row(typeA, bassA, chordA, melodyA, drumA, tempoA, priceA, keyShiftA)
    vecB = build_row(typeB, bassB, chordB, melodyB, drumB, tempoB, priceB, keyShiftB)

    # === 内外部選好 ===
    internal_pref_A = 1 if rankA < rankB else 0
    internal_pref_B = 1 if rankB < rankA else 0
    external_pref_A = 1 if rankA < rankExt else 0
    external_pref_B = 1 if rankB < rankExt else 0

    baseA = [participant["id"], participant["gender"], participant["age"], trial, internal_pref_A, external_pref_A]
    baseB = [participant["id"], participant["gender"], participant["age"], trial, internal_pref_B, external_pref_B]
    rowA = baseA + list(vecA.values())
    rowB = baseB + list(vecB.values())

    save_to_sheet("研究", "アンケート集計", rowA)
    save_to_sheet("研究", "アンケート集計", rowB)

    st.success(f"試行 {trial} の回答を保存しました。")

    if trial < TRIALS_PER_PERSON:
        st.session_state.trial += 1
        st.rerun()
    else:
        st.balloons()
        st.success("全ての試行が完了しました！")
