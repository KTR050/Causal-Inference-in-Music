import os
import random
import librosa
import numpy as np
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== フォルダ設定 ====
DATASET_FOLDER = "データセット"        # 曲ごとのフォルダ
DRUM_FOLDER = os.path.join(DATASET_FOLDER, "ドラム")
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [0.8, 1.2, 2]           # 速度変更オプション
price_options = [25, 50, 100]         # ランダム価格
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

# ==== ランダム曲選択 ====
songs = [d for d in os.listdir(DATASET_FOLDER) if os.path.isdir(os.path.join(DATASET_FOLDER, d)) and d != "ドラム"]
if len(songs) == 0:
    st.error("データセットに曲フォルダがありません。")
    st.stop()

song_choice = random.choice(songs)
key_choice = random.choice(["メジャー", "マイナー"])
base_path = os.path.join(DATASET_FOLDER, song_choice, key_choice)

# 各パートのランダム選択
def pick_random_file(folder):
    files = [f for f in os.listdir(folder) if f.endswith(".wav")]
    if not files:
        st.error(f"{folder} に wav ファイルがありません。")
        st.stop()
    return random.choice(files)

bass_file = pick_random_file(os.path.join(base_path, "ベース"))
chord_file = pick_random_file(os.path.join(base_path, "コード"))
melody_file = pick_random_file(os.path.join(base_path, "メロディ"))
drum_file = pick_random_file(DRUM_FOLDER)

# ==== 音声読み込み ====
def load_audio(path):
    y, sr = librosa.load(path, sr=None, mono=True)
    return y, sr

bass, sr = load_audio(os.path.join(base_path, "ベース", bass_file))
chord, _ = load_audio(os.path.join(base_path, "コード", chord_file))
melody, _ = load_audio(os.path.join(base_path, "メロディ", melody_file))
drum, _ = load_audio(os.path.join(DRUM_FOLDER, drum_file))

# ==== 長さ揃え & 合成 ====
min_len = min(len(bass), len(chord), len(melody), len(drum))
mix = bass[:min_len] + chord[:min_len] + melody[:min_len] + drum[:min_len]
mix = mix / np.max(np.abs(mix))  # 正規化

# ==== 一時ファイルに保存 ====
temp_file = os.path.join(TEMP_FOLDER, f"trial_{trial}.wav")
sf.write(temp_file, mix, sr)

# ==== Streamlit UI ====
st.audio(temp_file, format="audio/wav")
st.write(f"曲: {song_choice}, キー: {key_choice}")
st.write(f"ベース: {bass_file}, コード: {chord_file}, メロディ: {melody_file}, ドラム: {drum_file}")

# ランダム価格生成
priceA = random.choice(price_options)
priceB = random.choice(price_options)

# 選好順位入力
rank_options = [1, 2, 3]
rankA = st.selectbox("曲を買う", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("別曲を買う", rank_options, key=f"rankB_{trial}")
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
            song_choice, key_choice,
            bass_file, chord_file, melody_file, drum_file,
            priceA, rankA, priceB, rankB, rankExt
        ]
        save_to_sheet("研究", "アンケート集計", row)
        st.success(f"試行 {trial}/{TRIALS_PER_PERSON} の回答を保存しました。")

        if trial < TRIALS_PER_PERSON:
            st.session_state.trial += 1
            st.rerun()
        else:
            st.balloons()
            st.success("全ての試行が完了しました！")
