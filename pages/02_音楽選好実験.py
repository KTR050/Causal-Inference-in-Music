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

# ==== ランダム曲生成関数（ベース・コード・メロディ・ドラム合成＋ピッチ調整） ====
def generate_mix():
    # 曲タイプ選択
    song_choice = random.choice(["メジャー", "マイナー"])
    base_path = os.path.join(DATASET_FOLDER, song_choice)

    def pick_random_file(folder_name):
        folder_path = os.path.join(base_path, folder_name)
        files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
        return os.path.join(folder_path, random.choice(files))

    bass, sr = load_audio(pick_random_file("ベース"))
    chord, _ = load_audio(pick_random_file("コード"))
    melody, _ = load_audio(pick_random_file("メロディ"))
    
    # ドラムは共通フォルダ
    drum_folder = os.path.join(DATASET_FOLDER, "ドラム")
    drum_files = [f for f in os.listdir(drum_folder) if f.endswith(".wav")]
    drum, _ = load_audio(os.path.join(drum_folder, random.choice(drum_files)))

    # 長さ揃え & 合成
    min_len = min(len(bass), len(chord), len(melody), len(drum))
    mix = bass[:min_len] + chord[:min_len] + melody[:min_len] + drum[:min_len]
    mix = mix.astype(np.float32)

    # 合成後にテンポ変更（ピッチ調整）
    tempo = random.choice(bpm_options)
    if tempo != 1.0:
        mix = librosa.effects.time_stretch(mix, rate=tempo)
    
    # 正規化
    mix = mix / np.max(np.abs(mix))
    return mix, sr, song_choice, tempo, bass, chord, melody, drum

# ==== 曲A生成 ====
mixA, srA, typeA, tempoA, bassA, chordA, melodyA, drumA = generate_mix()
fileA = os.path.join(TEMP_FOLDER, f"trial_{trial}_A.wav")
sf.write(fileA, mixA, srA)
st.markdown("### 曲 A")
st.audio(fileA, format="audio/wav")

# ==== 曲B生成 ====
mixB, srB, typeB, tempoB, bassB, chordB, melodyB, drumB = generate_mix()
fileB = os.path.join(TEMP_FOLDER, f"trial_{trial}_B.wav")
sf.write(fileB, mixB, srB)
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
            participant["id"], participant["gender"], participant["age"],
            trial,
            # 曲A情報
            typeA, os.path.basename(bassA), os.path.basename(chordA),
            os.path.basename(melodyA), os.path.basename(drumA), tempoA, priceA, rankA,
            # 曲B情報
            typeB, os.path.basename(bassB), os.path.basename(chordB),
            os.path.basename(melodyB), os.path.basename(drumB), tempoB, priceB, rankB,
            # External Option
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
