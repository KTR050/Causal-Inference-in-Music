st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

# 🔽 サイドバー（自動ページリンク）を非表示にするCSS
hide_pages_css = """
<style>
    [data-testid="stSidebarNav"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
</style>
"""
st.markdown(hide_pages_css, unsafe_allow_html=True)

import streamlit as st

st.set_page_config(page_title="音楽選好実験", page_icon="🎵", layout="centered")

st.title("🎵 音楽選好実験へようこそ")
st.markdown("""
このアプリでは、音楽の聴取実験を行います。
@@ -14,3 +27,4 @@

st.page_link("pages/01_被験者登録.py", label="👉 被験者登録ページへ", icon="🧑‍💼")
