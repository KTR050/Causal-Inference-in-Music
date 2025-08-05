import os
import base64
import random
import librosa
import soundfile as sf
import numpy as np
import streamlit as st
from scipy.signal import butter, lfilter
from save_to_sheet import save_to_sheet

# ==== 相対調変換（#に統一）====
RELATIVE_KEY_SHIFT = {
    "C": ("A#m", -3), "A#m": ("C", 3),
    "C#": ("A#m", -3), "A#m": ("C#", 3),
    "D": ("Bm", -3), "Bm": ("D", 3),
    "D#": ("Cm", -3), "Cm": ("D#", 3),
    "E": ("C#m", -3), "C#m": ("E", 3),
    "F": ("Dm", -3), "Dm": ("F", 3),
    "F#": ("D#m", -3), "D#m": ("F#", 3),
    "G": ("Em", -3), "Em": ("G", 3),
    "G#": ("Fm", -3), "Fm": ("G#", 3),
    "A": ("F#m", -3), "F#m": ("A", 3),
    "A#": ("Gm", -3), "Gm": ("A#", 3),
    "B": ("G#m", -3), "G#m": ("B", 3)
}

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
bpm_options = [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
key_options = [-3, -2, -1, 0, 1, 2, 3]

# ==== ユーティリティ関数 ====
def extract_key_from_filename(filename):
    return filename.split("_")[0]

def extract_musicname_number(filename):
    parts = filename.split("_")
    return "_".join(parts[1:]).replace(".wav", "")

def get_mode(key_name):
    return "マイナー" if key_name.endswith("m") else "メジャー"

def get_mode_shift(original_key):
    if original_key in RELATIVE_KEY_SHIFT and random.choice([True, False]):
        _, shift = RELATIVE_KEY_SHIFT[original_key]
        return shift
    return 0

# ==== EQ 関数 ====
def butter_bandpass(lowcut, highcut, fs, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return butter(order, [low, high], btype='band')

def apply_filter(data, lowcut, highcut, fs, gain):
    b, a = butter_bandpass(lowcut, highcut, fs)
    filtered = lfilter(b, a, data)
    return filtered * gain

def apply_random_eq(y, sr):
    low_gain = np.random.uniform(0.9, 1.1)
    mid_gain = np.random.uniform(0.9, 1.1)
    high_gain = np.random.uniform(0.9, 1.1)

    low = apply_filter(y, 20, 250, sr, low_gain)
    mid = apply_filter(y, 250, 4000, sr, mid_gain)
    high = apply_filter(y, 4000, 16000, sr, high_gain)

    y_eq = low + mid + high
    y_eq = np.nan_to_num(y_eq)
    y_eq = np.clip(y_eq, -1.0, 1.0)
    y_eq = librosa.util.normalize(y_eq)

    eq_info = {
        "low": round(low_gain, 2),
        "mid": round(mid_gain, 2),
        "high": round(high_gain, 2)
    }
    return y_eq, eq_info

# ==== 音声処理 ====
def process_audio(input_path, tempo=1.0, key_shift=0, output_path="output.wav", base_key=None):
    y, sr = librosa.load(input_path, sr=None, mono=True)

    if tempo != 1.0:
        y = librosa.effects.time_stretch(y, rate=tempo)

    if base_key:
        key_shift += get_mode_shift(base_key)

    if key_shift != 0:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=key_shift)

    y_eq, eq_info = apply_random_eq(y, sr)
    sf.write(output_path, y_eq, sr)
    return eq_info

# ==== ループ再生対応 ====
def loop_audio_player(audio_path: str, label: str):
    audio_file = open(audio_path, "rb")
    audio_bytes = audio_file.read()
    b64_audio = base64.b64encode(audio_bytes).decode()
    audio_tag = f"""
    <h5>{label}</h5>
    <audio controls autoplay loop>
        <source src="data:audio/wav;base64,{b64_audio}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_tag, unsafe_allow_html=True)

# ==== 音声ファイル選択 ====
files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

file1 = random.choice(files)
tempo1 = random.choice(bpm_options)
pitch1 = random.choice(key_options)
key1 = extract_key_from_filename(file1)
mode1 = get_mode(key1)
musicname1 = extract_musicname_number(file1)

file2 = random.choice(files)
while file2 == file1:
    file2 = random.choice(files)
tempo2 = random.choice(bpm_options)
pitch2 = random.choice(key_options)
key2 = extract_key_from_filename(file2)
mode2 = get_mode(key2)
musicname2 = extract_musicname_number(file2)

# ==== 音声生成 ====
processed_file1 = os.path.join(TEMP_FOLDER, "processed1.wav")
processed_file2 = os.path.join(TEMP_FOLDER, "processed2.wav")

eq1 = process_audio(os.path.join(AUDIO_FOLDER, file1), tempo1, pitch1, processed_file1, key1)
eq2 = process_audio(os.path.join(AUDIO_FOLDER, file2), tempo2, pitch2, processed_file2, key2)

# ==== UI ====
st.title("音楽選好実験")

loop_audio_player(processed_file1, "選択肢 1")
st.text(f"曲名: {musicname1}, テンポ倍率: {tempo1}, キー変化: {pitch1:+}, モード: {mode1}")
st.text(f"EQ: 低={eq1['low']}, 中={eq1['mid']}, 高={eq1['high']}")

loop_audio_player(processed_file2, "選択肢 2")
st.text(f"曲名: {musicname2}, テンポ倍率: {tempo2}, キー変化: {pitch2:+}, モード: {mode2}")
st.text(f"EQ: 低={eq2['low']}, 中={eq2['mid']}, 高={eq2['high']}")

choice = st.radio("どちらが好みですか？", ["1", "2"])

if st.button("送信"):
    row = [
        musicname1, tempo1, pitch1, mode1, eq1['low'], eq1['mid'], eq1['high'],
        musicname2, tempo2, pitch2, mode2, eq2['low'], eq2['mid'], eq2['high'],
        int(choice)  # 数値として保存
    ]
    save_to_sheet("研究", "アンケート集計", row)
    st.success("✅ 回答がスプレッドシートに保存されました。ありがとうございました！")
