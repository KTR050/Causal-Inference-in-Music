import streamlit as st

st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

st.title("🎵 音楽選好実験へようこそ")
st.markdown("""
このアプリでは、音楽の聴取実験を行います。

1️⃣ まず「被験者登録」ページで性別と年齢を入力してください。  
2️⃣ その後、「音楽選好実験」に進みます。  

---
""")

st.page_link("pages/01_被験者登録.py", label="👉 被験者登録ページへ", icon="🧑‍💼")

