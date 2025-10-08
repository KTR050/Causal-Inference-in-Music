import os
import base64
import random
import uuid
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
    st.error("環境変数 GOOGLE_CREDENTIALS_B64 が設定されていません。")
    st.stop()

# ==== フォルダ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ==== パラメータ ====
# 元の設定を維持（倍率を広く取る）
bpm_options = [0.8, 1.0, 1.4, 2.2]
price_options = [50, 100, 200]

# ==== ユーティリティ関数 ====
def extract_musicname_number(filename):
    """ファイル名から拡張子を除去"""
    return os.path.splitext(filename)[0]

# ==== 音声処理（Soxを使用） ====
import sox
import soundfile as sf
import librosa

def process_audio(input_path, tempo=1.0, output_path="output.wav"):
    """
    Soxを使った高品質なテンポ変更。
    Rubberbandが使えない環境（Streamlit Cloud）でも安定動作。
    """
    try:
        # tempo=1.0なら単純コピー
        if tempo == 1.0:
            y, sr = librosa.load(input_path, sr=None, mono=True)
            sf.write(output_path, y, sr)
        else:
            tfm = sox.Transformer()
            tfm.tempo(tempo)
            tfm.build(input_path, output_path)
    except Exception as e:
        st.error(f"音声処理中にエラーが発生しました: {e}")
        raise


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

# ==== 一時ファイル（UUIDで一意名生成） ====
uid = uuid.uuid4().hex
processed_fileA = os.path.join(TEMP_FOLDER, f"processed_A_{uid}.wav")
processed_fileB = os.path.join(TEMP_FOLDER, f"processed_B_{uid}.wav")

process_audio(os.path.join(AUDIO_FOLDER, fileA), tempoA, processed_fileA)
process_audio(os.path.join(AUDIO_FOLDER, fileB), tempoB, processed_fileB)

# ==== UI ====
st.title("音楽選好実験（順位付け形式）")

st.markdown("""
### 🎧 以下の2曲を聴いてください。
そのうえで、**3つの選択肢（A, B, External Option）** に順位（1〜3）を付けてください。
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

# 順位選択
st.markdown("#### 順位を選択してください（1〜3の各数字は一度だけ使ってください）")
rank_options = [1, 2, 3]
rankA = st.selectbox("曲 A の順位", rank_options, key="rankA")
rankB = st.selectbox("曲 B の順位", rank_options, key="rankB")
rankExt = st.selectbox("External Option の順位", rank_options, key="rankExt")

# バリデーション
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
        try:
            save_to_sheet("研究", "アンケート集計", row)
            st.success("✅ 回答がスプレッドシートに保存されました。ありがとうございました！")
        except Exception as e:
            st.error(f"⚠️ スプレッドシート保存中にエラーが発生しました: {e}")
            # ローカルバックアップ
            try:
                with open("backup_responses.csv", "a", encoding="utf-8") as f:
                    f.write(",".join(map(str, row)) + "\n")
                st.info("ローカルにバックアップを保存しました。")
            except Exception as e2:
                st.error(f"バックアップ保存にも失敗しました: {e2}")


