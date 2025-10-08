import os
import base64
import random
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== Google認証情報 ====
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
TRIALS_PER_PERSON = 20  # 1人あたりの試行回数

# ==== 音声処理関数 ====
def extract_musicname_number(filename):
    return filename.replace(".wav", "")

def process_audio(input_path, tempo=1.0, output_path="output.wav"):
    """テンポ変更のみ"""
    y, sr = librosa.load(input_path, sr=None, mono=True)
    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)
    sf.write(output_path, y, sr)

# ==== セッション初期化 ====
if "participant_info" not in st.session_state:
    st.error("⚠️ 先に参加者情報を登録してください。")
    st.stop()

if "trial" not in st.session_state:
    st.session_state.trial = 1  # 現在の試行番号

participant = st.session_state.participant_info
trial = st.session_state.trial

# ==== UI ====
st.title(f"音楽選好実験（試行 {trial} / {TRIALS_PER_PERSON}）")

st.markdown("""
以下の2曲を聴いて、3つの選択肢に順位を付けてください。  
1 = 最も好ましい  
2 = 次に好ましい  
3 = 最も好ましくない
""")

# ==== 音声ファイルランダム選択 ====
files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

fileA = random.choice(files)
fileB = random.choice([f for f in files if f != fileA])
tempoA = random.choice(bpm_options)
tempoB = random.choice(bpm_options)
priceA = random.choice(price_options)
priceB = random.choice(price_options)

musicnameA = extract_musicname_number(fileA)
musicnameB = extract_musicname_number(fileB)

# ==== 音声ファイル生成 ====
processed_fileA = os.path.join(TEMP_FOLDER, "processed_A.wav")
processed_fileB = os.path.join(TEMP_FOLDER, "processed_B.wav")
process_audio(os.path.join(AUDIO_FOLDER, fileA), tempoA, processed_fileA)
process_audio(os.path.join(AUDIO_FOLDER, fileB), tempoB, processed_fileB)

# ==== 曲A ====
st.markdown(f"### 曲 A　（価格: {priceA} 円）")
st.audio(processed_fileA, format="audio/wav")

# ==== 曲B ====
st.markdown(f"### 曲 B　（価格: {priceB} 円）")
st.audio(processed_fileB, format="audio/wav")

# ==== 外部選択肢 ====
st.markdown("### External Option（どちらも買わない）")

rank_options = [1, 2, 3]
rankA = st.selectbox("曲 A を買う", rank_options, key=f"rankA_{trial}")
rankB = st.selectbox("曲 B を買う", rank_options, key=f"rankB_{trial}")
rankExt = st.selectbox("どちらも買わない", rank_options, key=f"rankExt_{trial}")

# ==== バリデーション ====
ranks = [rankA, rankB, rankExt]
valid = len(set(ranks)) == 3

# ==== 保存処理 ====
if st.button("送信"):
    if not valid:
        st.error("順位が重複しています。修正してください。")
    else:
        # 保存データ作成
        row = [
            participant["id"],        # 参加者ID
            participant["gender"],    # 性別（1=男,0=女）
            participant["age"],       # 年齢
            trial,                    # 試行番号
            musicnameA, tempoA, priceA, rankA,
            musicnameB, tempoB, priceB, rankB,
            rankExt
        ]

        save_to_sheet("研究", "アンケート集計", row)
        st.success(f"回答が保存されました！（試行 {trial}/{TRIALS_PER_PERSON}）")

        # 次の試行へ
        if trial < TRIALS_PER_PERSON:
            st.session_state.trial += 1
            st.rerun()
        else:
            st.balloons()
            st.success("すべての試行が完了しました。ご協力ありがとうございました！")
            st.session_state.trial = 1  # リセット
