import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json

# --- 1. CẤU HÌNH AI & BẢO MẬT ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "AIzaSyCT2wrDqYloD2ZyhR3ZYvCkaYTsfM1t_ew"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. QUẢN LÝ SESSION ---
keys = ['score', 'streak', 'student_name', 'current_data', 'answered_status', 'notes']
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = 0 if k in ['score', 'streak'] else ({} if k == 'answered_status' else "")

# --- 3. GIAO DIỆN (GIỮ NGUYÊN TIÊU ĐỀ 70PX & NOTE 750PX) ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide", page_icon="🛡️")

st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #58a6ff !important; text-align: center; }}
    .note-box textarea {{ height: 750px !important; background-color: #161b22 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; }}
    .check-box {{ background-color: #161b22; border-left: 15px solid #0056b3; padding: 35px; border-radius: 15px; }}
    .stSidebar {{ background-color: #0d1117 !important; }}
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (PROFILE & ĐIỂM SỐ) ---
with st.sidebar:
    st.markdown("## 🛡️ SMARTLENS")
    if not st.session_name:
        st.session_state.student_name = st.text_input("👤 Tên học sinh:", key="st_user")
    else:
        st.markdown(f"Chào: **{st.session_state.student_name}**")
    
    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #0056b3;">
            <p style="font-size: 12px;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 60px !important; margin: 0;">{st.session_state.score}</h1>
            <p style="font-size: 12px;">CHUỖI HỌC TẬP</p>
            <h2 style="color: #ff4b4b; font-size: 40px !important; margin: 0;">{st.session_state.streak} 🔥</h2>
        </div>
    """, unsafe_allow_html=True)

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)
m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("### 📝 GHI CHÚ (750PX)")
    st.session_state.notes = st.text_area("", value=st.session_state.notes, key="note_v14", placeholder="Ghi lại ý tưởng phản biện...")

with m_col:
    tab1, tab2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])
    
    with tab1:
        url = st.text_input("1. Dán link YouTube vào đây:", placeholder="https://youtube.com/...")
        
        st.markdown("---")
        st.markdown("### 🛠️ BƯỚC XỬ LÝ (Dành cho Giám khảo)")
        st.write("Do chính sách bảo mật của YouTube, vui lòng làm theo 2 bước nhanh sau:")
        
        # Nút hỗ trợ lấy Transcript nhanh
        if url:
            v_id_match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_id_match:
                v_id = v_id_match.group(1)
                st.link_button("👉 BƯỚC 1: NHẤN ĐỂ LẤY VĂN BẢN VIDEO", f"https://downsub.com/?url={url}")
        
        transcript_input = st.text_area("2. Dán nội dung văn bản vừa lấy được vào đây:", height=200)
        
        if st.button("🚀 BẮT ĐẦU THẨM ĐỊNH BẰNG AI"):
            if transcript_input:
                with st.spinner("AI đang phân tích đa chiều..."):
                    prompt = f"Phân tích tiếng Việt (Xác thực, Phản biện, Mở rộng) + 5 câu hỏi JSON: {transcript_input[:5000]}"
                    try:
                        res = model.generate_content(prompt)
                        data = json.loads(re.search(r"\{.*\}", res.text, re.DOTALL).group())
                        st.session_state.current_data = data
                        st.rerun()
                    except: st.error("Lỗi xử lý dữ liệu AI.")
            else:
                st.warning("Vui lòng dán văn bản video ở Bước 2.")

    with tab2:
        direct_txt = st.text_area("Dán đoạn văn bản cần kiểm chứng:", height=300)
        if st.button("🔍 KIỂM CHỨNG NGAY"):
            # Logic tương tự analyze văn bản...
            pass

    # HIỂN THỊ KẾT QUẢ (GIỮ NGUYÊN)
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("---")
        st.markdown(f'<div class="check-box">{d["verification"]}</div>', unsafe_allow_html=True)
        # Quiz...
