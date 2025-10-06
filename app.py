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

# ==== パラメータ ====
bpm_options = [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
price_options = [50, 100, 200, 400]

# ==== ユーティリティ関数 ====
def extract_musicname_number(filename):
    parts = filename.split("_")
    return "_".join(parts).replace(".wav", "")

# ==== 音声処理（テンポ変更のみ、キャッシュ付き） ====
@st.cache_data
def load_and_process_audio(file_path, tempo):
    y, sr = librosa.load(file_path, sr=None, mono=True)
    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)
    temp_path = os.path.join(TEMP_FOLDER, f"{tempo}_{os.path.basename(file_path)}")
    sf.write(temp_path, y, sr)
    return temp_path

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

# ==== 音声生成（キャッシュ利用） ====
processed_fileA = load_and_process_audio(os.path.join(AUDIO_FOLDER, fileA), tempoA)
processed_fileB = load_and_process_audio(os.path.join(AUDIO_FOLDER, fileB), tempoB)

# ==== UI ====
st.title("音楽選好実験（順位付け形式）")

st.markdown("""
以下の2曲を聴いてください。そのうえで、3つの選択肢（曲A, 曲B, External Option）に順位（1〜3）を付けてください。
- 1 = 最も好ましい
- 2 = 次に好ましい
- 3 = 最も好ましくない
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
st.markdown("### External Option（どちらも好まないなど）")

# プルダウン選択（順位付け）
st.markdown("#### 順位を選択してください（1〜3の各数字は一度だけ使ってください）")
rank_options = [1, 2, 3]
rankA = st.selectbox("曲 A の順位", rank_options, key="rankA")
rankB = st.selectbox("曲 B の順位", rank_options, key="rankB")
rankExt = st.selectbox("External Option の順位", rank_options, key="rankExt")

# バリデーション（重複チェック）
ranks = [rankA, rankB, rankExt]
if len(set(ranks)) < 3:
    st.warning("⚠️ 各順位（1, 2, 3）は一度ずつ使用してください。")
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
        st.success("✅ 回答がスプレッドシートに保存されました。ありがとうございました！")
