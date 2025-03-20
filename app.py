import streamlit as st
import subprocess
import pandas as pd
import json
import sys

st.set_page_config(page_title="🦉 Parsifly", layout="centered")

# Logo and header clearly defined
st.markdown("<h1 style='text-align: center;'>🦉 Parsifly - TikTok Analyzer</h1>", unsafe_allow_html=True)
st.markdown("---")

# Input fields clearly styled
with st.form("analysis_form"):
    url = st.text_input("🔗 Enter TikTok Profile URL:")
    num_videos = st.slider("📊 Number of Videos to Analyze:", 10, 100, 10)
    submit_button = st.form_submit_button(label="🚀 Analyze")

if submit_button:
    with st.spinner("✨ Analyzing, please wait..."):
        try:
            subprocess.run([sys.executable, "tiktok_scraper.py", url, str(num_videos)], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Error: {e.stderr}")
            st.stop()

        try:
            with open("tiktok_results.json", "r", encoding="utf-8") as f:
                video_data = json.load(f)
        except FileNotFoundError:
            st.error("❌ Results file not found. Try again.")
            st.stop()

        df = pd.DataFrame(video_data)
        df.index = df.index + 1
        df.index.name = 'No.'

    st.success("✅ Analysis completed!")
    st.dataframe(df, use_container_width=True)

    excel_filename = "tiktok_data.xlsx"
    df.to_excel(excel_filename, index=True)

    with open(excel_filename, "rb") as file:
        st.download_button(
            label="📥 Download Excel Sheet",
            data=file,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")
st.markdown("<p style='text-align: center;'>Made with ❤️ by Parsifly</p>", unsafe_allow_html=True)
