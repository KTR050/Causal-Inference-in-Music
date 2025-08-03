import os
import base64
import random
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# === credentials.json を生成 ===
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))
else:
    raise FileNotFoundError("環境変数 GOOGLE_CREDENTIALS_B64 が見つかりません。Streamlit Cloud の Secrets に設定してください。")

# === フォルダ設定 ===
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# === ファイルとパラメータの取得 ===
files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]
bpm_options = [0.8, 1.0, 1.2, 1.4, 1.6]
key_options = [-3, -2, -1, 0, 1, 2, 3]

# === 音声処理関数 ===
def process_audio(input_path, tempo=1.0, key_shift=0, output_path="output.wav"):
    y, sr = librosa.load(input_path, sr=None)
    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)
    if key_shift != 0:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=key_shift)
    sf.write(output_path, y, sr)

# === ランダム選曲と変換 ===
file1 = random.choice(files)
tempo1 = random.choice(bpm_options)
key1 = random.choice(key_options)

file2 = random.choice(files)
while file2 == file1:
    file2 = random.choice(files)
tempo2 = random.choice(bpm_options)
key2 = random.choice(key_options)

processed_file1 = os.path.join(TEMP_FOLDER, "processed1.wav")
processed_file2 = os.path.join(TEMP_FOLDER, "processed2.wav")

process_audio(os.path.join(AUDIO_FOLDER, file1), tempo1, key1, processed_file1)
process_audio(os.path.join(AUDIO_FOLDER, file2), tempo2, key2, processed_file2)

# === Streamlit UI ===
st.title("音楽選好実験")

st.subheader("選択肢 1")
st.audio(processed_file1)
st.text(f"テンポ倍率: {tempo1}, キー変化: {key1:+}")

st.subheader("選択肢 2")
st.audio(processed_file2)
st.text(f"テンポ倍率: {tempo2}, キー変化: {key2:+}")

choice = st.radio("どちらが好みですか？", ["1", "2"])

if st.button("送信"):
    row = [file1, tempo1, key1, file2, tempo2, key2, choice]
    save_to_sheet("研究", "アンケート集計", row)
    st.success("回答がスプレッドシートに保存されました。ありがとうございました！")
