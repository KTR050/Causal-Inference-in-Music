import base64
import os

# 環境変数から Base64 文字列を取得（GitHub Actions など）
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")

# Base64 を decode してファイルに保存
if b64_creds:
    with open("credentials.json", "wb") as f:
        f.write(base64.b64decode(b64_creds))

import streamlit as st
import os
import random
from save_to_sheet import save_to_sheet

AUDIO_FOLDER = "データセット"
files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

bpm_options = [0.8, 1.0, 1.2, 1.4, 1.6]
key_options = [-3, -2, -1, 0, 1, 2, 3]

# ランダムに2曲選択
file1, file2 = random.sample(files, 2)
tempo1, tempo2 = random.choice(bpm_options), random.choice(bpm_options)
key1, key2 = random.choice(key_options), random.choice(key_options)

st.title("音楽選好実験")

st.subheader("選択肢 1")
st.audio(os.path.join(AUDIO_FOLDER, file1))
st.text(f"テンポ倍率: {tempo1}, キー変化: {key1}")

st.subheader("選択肢 2")
st.audio(os.path.join(AUDIO_FOLDER, file2))
st.text(f"テンポ倍率: {tempo2}, キー変化: {key2}")

choice = st.radio("どちらが好みですか？", ["1", "2"])

if st.button("送信"):
    row = [file1, tempo1, key1, file2, tempo2, key2, choice]
    save_to_sheet("研究", "アンケート集計", row)
    st.success("回答がスプレッドシートに保存されました。ありがとうございました！")

