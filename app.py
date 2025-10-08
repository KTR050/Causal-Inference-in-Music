import os
import base64
import random
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== 認証情報 ====
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))
else:
    raise FileNotFoundError("GOOGLE_CREDENTIALS_B64 が設定されていません。")

# ==== フォルダ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ==== パラメータ ====
bpm_options = [0.8, 1.0, 1.4, 2.2]
price_options = [50, 100, 200]

# ==== ユーティリティ関数 ====
def extract_musicname_number(filename):
    parts = filename.split("_")
    return "_".join(parts).replace(".wav", "")

# ==== 音声処理（テンポ変更のみ） ====
def process_audio(input_path, tempo=1.0, output_path="output.wav"):
    y, sr = librosa.load(input_path, sr=None, mono=True)
    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)
    sf.write(output_path, y, sr)

# ==== 音声ファイル選択 ====
files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

fileA = random.choice(files)
tempoA = random.choice(bpm_options)
musicnameA = extract_musicname_number(fileA)

fileB = random.choice(files)
while fileB == fileA:
    fileB = random.choice(files)
tempoB = random.choice(bpm_options)
musicnameB = extract_musicname_number(fileB)

# ==== ランダム価格生成 ====
priceA = random.choice(price_options)
priceB = random.choice(price_options)

# ==== 音声生成 ====
processed_fileA = os.path.join(TEMP_FOLDER, "processed_A.wav")
processed_fileB = os.path.join(TEMP_FOLDER, "processed_B.wav")

process_audio(os.path.join(AUDIO_FOLDER, fileA), tempoA, processed_fileA)
process_audio(os.path.join(AUDIO_FOLDER, fileB), tempoB, processed_fileB)

# ==== UI ====
st.title("音楽選好実験")

st.markdown("""
以下の2曲を聴いてください。
そのうえで、3つの選択肢 に順位を付けてください。
""")

# 曲A
st.markdown(f"### 曲 A")
st.markdown(f"価格: {priceA} 円")
st.audio(processed_fileA, format="audio/wav")

# 曲B
st.markdown(f"### 曲 B")
st.markdown(f"価格: {priceB} 円")
st.audio(processed_fileB, format="audio/wav")

# External Option
st.markdown("External Option（どちらも買わない）")

# プルダウン選択（順位付け）
st.markdown("""
順位を選択してください（1〜3の各数字は一度だけ使ってください）
1 = 最も好ましい  
2 = 次に好ましい  
3 = 最も好ましくない  
         """)
rank_options = [1, 2, 3]
rankA = st.selectbox("曲 A を買う", rank_options, key="rankA")
rankB = st.selectbox("曲 B を買う", rank_options, key="rankB")
rankExt = st.selectbox("どちらも買わない", rank_options, key="rankExt")

# バリデーション（重複チェック）
ranks = [rankA, rankB, rankExt]
if len(set(ranks)) < 3:
    st.warning("各順位（1, 2, 3）は一度ずつ使用してください。")
    valid = False
else:
    valid = True

# ==== 保存処理 ====
if st.button("送信"):
    if not valid:
        st.error("順位が重複しています。修正してください。")
    else:
        row = [
            musicnameA, tempoA, priceA, rankA,
            musicnameB, tempoB, priceB, rankB,
            rankExt
        ]
        save_to_sheet("研究", "アンケート集計", row)
        st.success("回答がスプレッドシートに保存されました。ありがとうございました！")




