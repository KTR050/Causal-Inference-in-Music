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

bpm_options = [0.8, 1.2, 2]       # ピッチ/テンポ倍率
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

# ==== 曲タイプ選択（メジャー/マイナー） ====
song_choice = random.choice(["メジャー", "マイナー"])
base_path = os.path.join(DATASET_FOLDER, song_choice)

# ==== パートごとのランダム選択関数 ====
def pick_random_file(folder_name):
    folder_path = os.path.join(base_path, folder_name)
    if not os.path.exists(folder_path):
        st.error(f"{folder_name} フォルダが存在しません: {folder_path}")
        st.stop()
    files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
    if not files:
        st.error(f"{folder_name} フォルダに WAV ファイルがありません: {folder_path}")
        st.stop()
    return os.path.join(folder_path, random.choice(files))

bass_file = pick_random_file("ベース")
chord_file = pick_random_file("コード")
melody_file = pick_random_file("メロディ")

# ==== ドラムファイル選択 ====
drum_folder = os.path.join(DATASET_FOLDER, "ドラム")
drum_files = [f for f in os.listdir(drum_folder) if f.endswith(".wav")]
if not drum_files:
    st.error(f"ドラムフォルダに WAV ファイルがありません: {drum_folder}")
    st.stop()
drum_file = os.path.join(drum_folder, random.choice(drum_files))

# ==== 音声読み込み ====
def load_audio(path):
    y, sr = librosa.load(path, sr=None, mono=True)
    return y, sr

bass, sr = load_audio(bass_file)
chord, _ = load_audio(chord_file)
melody, _ = load_audio(melody_file)
drum, _ = load_audio(drum_file)

# ==== 長さ揃え & 合成 ====
min_len = min(len(bass), len(chord), len(melody), len(drum))
mix = bass[:min_len] + chord[:min_len] + melody[:min_len] + drum[:min_len]

# float32に変換
mix = mix.astype(np.float32)

# ==== 合成後にテンポ変更（ピッチ調整） ====
tempo = random.choice(bpm_options)
if tempo != 1.0:
    mix = librosa.effects.time_stretch(mix, rate=tempo)

# 正規化
mix = mix / np.max(np.abs(mix))

# 保存
temp_file = os.path.join(TEMP_FOLDER, f"trial_{trial}.wav")
sf.write(temp_file, mix, sr)


# ==== Streamlit UI ====
st.audio(temp_file, format="audio/wav")
st.write(f"曲タイプ: {song_choice}, テンポ倍率: {tempo}")
st.write(f"ベース: {os.path.basename(bass_file)}, コード: {os.path.basename(chord_file)}, メロディ: {os.path.basename(melody_file)}, ドラム: {os.path.basename(drum_file)}")

# ==== ランダム価格生成 ====
priceA = random.choice(price_options)
priceB = random.choice(price_options)

# ==== 選好順位入力 ====
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
            song_choice,
            os.path.basename(bass_file), os.path.basename(chord_file),
            os.path.basename(melody_file), os.path.basename(drum_file),
            tempo,
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
