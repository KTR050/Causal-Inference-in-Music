import streamlit as st
import random
import os
import librosa
import soundfile as sf

# ==== 設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

bpm_options = [0.8, 1.0, 1.4, 2.2]
price_options = [50, 100, 200]

files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

def extract_musicname_number(filename):
    parts = filename.split("_")
    return "_".join(parts).replace(".wav", "")

def process_audio(input_path, tempo=1.0, output_path="output.wav"):
    y, sr = librosa.load(input_path, sr=None, mono=True)
    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)
    sf.write(output_path, y, sr)

# ==== ランダム生成関数 ====
def generate_new_trial():
    fileA = random.choice(files)
    fileB = random.choice(files)
    while fileB == fileA:
        fileB = random.choice(files)

    tempoA = random.choice(bpm_options)
    tempoB = random.choice(bpm_options)
    priceA = random.choice(price_options)
    priceB = random.choice(price_options)
    musicnameA = extract_musicname_number(fileA)
    musicnameB = extract_musicname_number(fileB)

    processed_fileA = os.path.join(TEMP_FOLDER, "processed_A.wav")
    processed_fileB = os.path.join(TEMP_FOLDER, "processed_B.wav")

    process_audio(os.path.join(AUDIO_FOLDER, fileA), tempoA, processed_fileA)
    process_audio(os.path.join(AUDIO_FOLDER, fileB), tempoB, processed_fileB)

    return {
        "fileA": processed_fileA,
        "fileB": processed_fileB,
        "musicnameA": musicnameA,
        "musicnameB": musicnameB,
        "tempoA": tempoA,
        "tempoB": tempoB,
        "priceA": priceA,
        "priceB": priceB
    }

# ==== セッションステート初期化 ====
if "trial" not in st.session_state:
    st.session_state.trial = generate_new_trial()

st.title("音楽選好実験")

trial = st.session_state.trial

st.markdown("""
以下の2曲を聴いてください。
そのうえで、3つの選択肢に順位を付けてください。
""")

# 曲A
st.markdown(f"### 曲 A")
st.markdown(f"価格: {trial['priceA']} 円")
st.audio(trial['fileA'], format="audio/wav")

# 曲B
st.markdown(f"### 曲 B")
st.markdown(f"価格: {trial['priceB']} 円")
st.audio(trial['fileB'], format="audio/wav")

# External Option
st.markdown("External Option（どちらも買わない）")

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
valid = len(set(ranks)) == 3
if not valid:
    st.warning("各順位（1, 2, 3）は一度ずつ使用してください。")

# ==== 送信ボタン ====
if st.button("送信"):
    if not valid:
        st.error("順位が重複しています。修正してください。")
    else:
        # 保存処理
        row = [
            trial['musicnameA'], trial['tempoA'], trial['priceA'], rankA,
            trial['musicnameB'], trial['tempoB'], trial['priceB'], rankB,
            rankExt
        ]
        # save_to_sheet(...)

        st.success("回答が保存されました！新しい曲を表示します。")

        # 新しい試行を生成
        st.session_state.trial = generate_new_trial()

        # page rerun して selectbox を初期化
        st.experimental_rerun()



