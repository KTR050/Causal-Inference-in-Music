import os
import random
import librosa
import numpy as np
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== フォルダ設定 ====
DATASET_FOLDER = "データセット"   # メジャー/マイナー/ドラム
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [0.8, 1, 1.4]       # ピッチ/テンポ倍率
price_options = [25, 50, 100]
TRIALS_PER_PERSON = 10

# ==== セッションチェック ====
if "participant_info" not in st.session_state:
    st.error("⚠️ 先に登録ページで情報を入力してください")
    st.stop()

if "trial" not in st.session_state:
    st.session_state.trial = 1

participant = st.session_state.participant_info
trial = st.session_state.trial

st.title(f"音楽選好実験（試行 {trial}/{TRIALS_PER_PERSON}）")

# ==== 音声読み込み関数 ====
def load_audio(path):
    y, sr = librosa.load(path, sr=None, mono=True)
    return y, sr

# ==== ランダムファイル選択 ====
def pick_random_file(folder):
    files = [f for f in os.listdir(folder) if f.endswith(".wav")]
    return os.path.join(folder, random.choice(files))

def pick_random_track_files(song_type):
    base_path = os.path.join(DATASET_FOLDER, song_type)
    bass_file = pick_random_file(os.path.join(base_path, "ベース"))
    chord_file = pick_random_file(os.path.join(base_path, "コード"))
    melody_file = pick_random_file(os.path.join(base_path, "メロディ"))
    return bass_file, chord_file, melody_file

def pick_random_drum_file():
    drum_folder = os.path.join(DATASET_FOLDER, "ドラム")
    return pick_random_file(drum_folder)

# ==== 曲生成（合成 + テンポ変更 + 正規化）====
def generate_mix(bass_file, chord_file, melody_file, drum_file):
    bass, sr = load_audio(bass_file)
    chord, _ = load_audio(chord_file)
    melody, _ = load_audio(melody_file)
    drum, _ = load_audio(drum_file)

    # 長さを min_len に揃えて合成
    min_len = min(len(bass), len(chord), len(melody), len(drum))
    mix = bass[:min_len] + chord[:min_len] + melody[:min_len] + drum[:min_len]
    mix = mix.astype(np.float32)

    # 合成後にテンポ変更
    tempo = random.choice(bpm_options)
    if tempo != 1.0:
        mix = librosa.effects.time_stretch(mix, rate=tempo)

    # 正規化
    mix = mix / np.max(np.abs(mix))
    return mix, sr, tempo

# ==== 曲A/B生成（初回のみ）====
if "mixA" not in st.session_state:
    typeA = random.choice(["メジャー", "マイナー"])
    bassA_file, chordA_file, melodyA_file = pick_random_track_files(typeA)
    drumA_file = pick_random_drum_file()
    mixA, srA, tempoA = generate_mix(bassA_file, chordA_file, melodyA_file, drumA_file)

    st.session_state.update({
        "mixA": mixA, "srA": srA, "typeA": typeA, "tempoA": tempoA,
        "bassA_file": bassA_file, "chordA_file": chordA_file,
        "melodyA_file": melodyA_file, "drumA_file": drumA_file
    })

if "mixB" not in st.session_state:
    typeB = random.choice(["メジャー", "マイナー"])
    bassB_file, chordB_file, melodyB_file = pick_random_track_files(typeB)
    drumB_file = pick_random_drum_file()
    mixB, srB, tempoB = generate_mix(bassB_file, chordB_file, melodyB_file, drumB_file)

    st.session_state.update({
        "mixB": mixB, "srB": srB, "typeB": typeB, "tempoB": tempoB,
        "bassB_file": bassB_file, "chordB_file": chordB_file,
        "melodyB_file": melodyB_file, "drumB_file": drumB_file
    })

# ==== 曲A/B保存 & 再生 ====
fileA = os.path.join(TEMP_FOLDER, f"trial_{trial}_A.wav")
sf.write(fileA, st.session_state.mixA, st.session_state.srA)
st.markdown("### 曲 A")
st.audio(fileA, format="audio/wav")

fileB = os.path.join(TEMP_FOLDER, f"trial_{trial}_B.wav")
sf.write(fileB, st.session_state.mixB, st.session_state.srB)
st.markdown("### 曲 B")
st.audio(fileB, format="audio/wav")

# ==== ランダム価格生成 ====
priceA = random.choice(price_options)
priceB = random.choice(price_options)
st.write(f"価格A: {priceA} 円, 価格B: {priceB} 円")

# ==== 選好順位入力 ====
rank_options = [1, 2, 3]
rankA = st.selectbox("曲Aを買う", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("曲Bを買う", rank_options, key=f"rankB_{trial}")
rankExt = st.selectbox("どちらも買わない", rank_options, key=f"rankExt_{trial}")

ranks = [rankA, rankB, rankExt]
valid = len(set(ranks)) == 3

# ==== 保存ボタン ====
if st.button("送信"):
    if not valid:
        st.error("順位が重複しています。")
    else:
        row = [
            # 曲A
            os.path.basename(st.session_state.bassA_file),
            os.path.basename(st.session_state.chordA_file),
            os.path.basename(st.session_state.melodyA_file),
            os.path.basename(st.session_state.drumA_file),
            priceA,
            st.session_state.tempoA,
            rankA,
            # 曲B
            os.path.basename(st.session_state.bassB_file),
            os.path.basename(st.session_state.chordB_file),
            os.path.basename(st.session_state.melodyB_file),
            os.path.basename(st.session_state.drumB_file),
            priceB,
            st.session_state.tempoB,
            rankB,
            # 外部オプション
            rankExt
        ]
        save_to_sheet("研究", "アンケート集計", row)
        st.success(f"試行 {trial}/{TRIALS_PER_PERSON} の回答を保存しました。")

        if trial < TRIALS_PER_PERSON:
            st.session_state.trial += 1
            # 曲A/Bをクリアして次の試行で新曲生成
            for key in ["mixA","srA","typeA","tempoA","bassA_file","chordA_file","melodyA_file","drumA_file",
                        "mixB","srB","typeB","tempoB","bassB_file","chordB_file","melodyB_file","drumB_file"]:
                st.session_state.pop(key, None)
            st.rerun()
        else:
            st.balloons()
            st.success("全ての試行が完了しました！")
