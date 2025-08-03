import os
import base64
import random
import librosa
import soundfile as sf
import streamlit as st
from save_to_sheet import save_to_sheet

# ==== 相対調シフト辞書 ====
RELATIVE_KEY_SHIFT = {
    "C": ("Am", -3), "Am": ("C", 3),
    "G": ("Em", -3), "Em": ("G", 3),
    "D": ("Bm", -3), "Bm": ("D", 3),
    "A": ("F#m", -3), "F#m": ("A", 3),
    "E": ("C#m", -3), "C#m": ("E", 3),
    "F": ("Dm", -3), "Dm": ("F", 3),
    "Bb": ("Gm", -3), "Gm": ("Bb", 3),
    "Eb": ("Cm", -3), "Cm": ("Eb", 3)
}

# ==== 環境変数から認証情報を生成 ====
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))
else:
    raise FileNotFoundError("環境変数 GOOGLE_CREDENTIALS_B64 が見つかりません。Streamlit Cloud の Secrets に設定してください。")

# ==== ディレクトリ設定 ====
AUDIO_FOLDER = "データセット"
TEMP_FOLDER = "temp_audio"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ==== 処理パラメータ ====
bpm_options = [0.8, 1.0, 1.2, 1.4]
key_options = [-2, -1, 0, 1, 2]

# ==== ファイルからキーを抽出 ====
def extract_key_from_filename(filename):
    # 例: "Dm_01_sample.wav" → "Dm"
    return filename.split("_")[0]

# ==== ランダムに長調↔短調を変換 ====
def get_mode_shift(original_key):
    if original_key in RELATIVE_KEY_SHIFT and random.choice([True, False]):
        _, shift = RELATIVE_KEY_SHIFT[original_key]
        return shift
    return 0

# ==== 音声処理 ====
def process_audio(input_path, tempo=1.0, key_shift=0, output_path="output.wav", base_key=None):
    y, sr = librosa.load(input_path, sr=None)
    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)
    if base_key:
        mode_shift = get_mode_shift(base_key)
        key_shift += mode_shift
    if key_shift != 0:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=key_shift)
    sf.write(output_path, y, sr)

# ==== ファイル一覧取得 ====
files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

# ==== ランダムに2ファイルを選択 ====
file1 = random.choice(files)
tempo1 = random.choice(bpm_options)
pitch1 = random.choice(key_options)
key1 = extract_key_from_filename(file1)

file2 = random.choice(files)
while file2 == file1:
    file2 = random.choice(files)
tempo2 = random.choice(bpm_options)
pitch2 = random.choice(key_options)
key2 = extract_key_from_filename(file2)

# ==== 処理ファイル保存先 ====
processed_file1 = os.path.join(TEMP_FOLDER, "processed1.wav")
processed_file2 = os.path.join(TEMP_FOLDER, "processed2.wav")

# ==== 音声ファイル処理 ====
process_audio(os.path.join(AUDIO_FOLDER, file1), tempo1, pitch1, processed_file1, base_key=key1)
process_audio(os.path.join(AUDIO_FOLDER, file2), tempo2, pitch2, processed_file2, base_key=key2)

# ==== Streamlit UI ====
st.title("🎵 音楽選好実験")

st.subheader("🔊 選択肢 1")
st.audio(processed_file1)
st.text(f"テンポ倍率: {tempo1}, ピッチシフト: {pitch1:+}, 原キー: {key1}")

st.subheader("🔊 選択肢 2")
st.audio(processed_file2)
st.text(f"テンポ倍率: {tempo2}, ピッチシフト: {pitch2:+}, 原キー: {key2}")

choice = st.radio("どちらが好みですか？", ["1", "2"])

if st.button("送信"):
    row = [file1, tempo1, pitch1, key1, file2, tempo2, pitch2, key2, choice]
    save_to_sheet("研究", "アンケート集計", row)
    st.success("✅ 回答がスプレッドシートに保存されました。ありがとうございました！")
