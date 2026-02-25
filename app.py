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

# --- 2. QUẢN LÝ SESSION STATE (SỬA LỖI TẠI ĐÂY) ---
keys = ['score', 'streak', 'student_name', 'current_data', 'answered_status', 'notes']
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = 0 if k in ['score', 'streak'] else ({} if k == 'answered_status' else "")

# --- 3. GIAO DIỆN CSS (70PX & 750PX) ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide", page_icon="🛡️")

st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #58a6ff !important; text-align: center; line-height: 1.1; }}
    .note-box textarea {{ height: 750px !important; background-color: #161b22 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; font-size: 16px !important; }}
    .check-box {{ background-color: #161b22; border-left: 15px solid #0056b3; padding: 35px; border-radius: 15px; line-height: 1.6; }}
    [data-testid="stSidebar"] {{ background-color: #0d1117 !important; border-right: 1px solid #30363d; }}
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (PROFILE & ĐIỂM SỐ) ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 40px !important;'>🛡️ SMARTLENS</h1>", unsafe_allow_html=True)
    
    # SỬA LỖI: Kiểm tra student_name trong session_state
    if not st.session_state.student_name:
        name_input = st.text_input("👤 Nhập tên học sinh:", key="name_reg")
        if name_input:
            st.session_state.student_name = name_input
            st.rerun()
    else:
        st.markdown(f"### Học sinh: <span style='color:#58a6ff'>{st.session_state.student_name}</span>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 25px; border-radius: 15px; border: 2px solid #0056b3; margin-top: 20px;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold; margin-bottom: 5px;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 70px !important; margin: 0; padding: 0;">{st.session_state.score}</h1>
            <hr style="border: 0.5px solid #30363d; margin: 15px 0;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold; margin-bottom: 5px;">STREAK</p>
            <h2 style="color: #ff4b4b; font-size: 50px !important; margin: 0; text-align: center;">{st.session_state.streak} 🔥</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ Bài học mới", use_container_width=True):
        st.session_state.current_data = ""
        st.session_state.answered_status = {}
        st.rerun()

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)

m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("### 📝 GHI CHÚ PHẢN BIỆN")
    st.markdown('<div class="note-box">', unsafe_allow_html=True)
    st.session_state.notes = st.text_area("", value=st.session_state.notes, key="note_v15", placeholder="Ghi lại ý tưởng tại đây...")
    st.markdown('</div>', unsafe_allow_html=True)

with m_col:
    tab1, tab2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])
    
    with tab1:
        st.info("💡 **Dành cho Giám khảo:** Nếu hệ thống không thể tự lấy phụ đề, vui lòng dùng nút Bước 1 để lấy văn bản nhanh.")
        url = st.text_input("Dán link YouTube:", placeholder="https://youtube.com/watch?v=...", key="yt_url")
        
        # Nút hỗ trợ Proxy lấy Transcript
        if url:
            v_match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_match:
                st.link_button("👉 BƯỚC 1: LẤY VĂN BẢN VIDEO (NHẤN VÀO ĐÂY)", f"https://downsub.com/?url={url}")
        
        transcript_input = st.text_area("BƯỚC 2: Dán nội dung văn bản vào đây:", height=180, key="ts_input")
        
        if st.button("🚀 BẮT ĐẦU THẨM ĐỊNH", type="primary"):
            if transcript_input:
                with st.spinner("AI đang mổ xẻ nội dung..."):
                    prompt = f"Phân tích tiếng Việt (Xác thực, Phản biện, Mở rộng) + 5 câu hỏi JSON: {transcript_input[:5000]}"
                    try:
                        res = model.generate_content(prompt)
                        match = re.search(r"\{.*\}", res.text, re.DOTALL)
                        st.session_state.current_data = json.loads(match.group())
                        st.rerun()
                    except: st.error("Lỗi: AI không thể đọc được cấu trúc văn bản này.")
            else: st.warning("Vui lòng dán văn bản video ở Bước 2.")

    with tab2:
        direct_text = st.text_area("Dán đoạn văn bản cần kiểm chứng:", height=300, key="direct_input")
        if st.button("🔍 KIỂM CHỨNG NGAY"):
            with st.spinner("Đang đối soát..."):
                prompt = f"Phân tích tiếng Việt (Xác thực, Phản biện, Mở rộng) + 5 câu hỏi JSON: {direct_text[:5000]}"
                try:
                    res = model.generate_content(prompt)
                    match = re.search(r"\{.*\}", res.text, re.DOTALL)
                    st.session_state.current_data = json.loads(match.group())
                    st.rerun()
                except: st.error("Lỗi xử lý AI.")

    # --- 6. HIỂN THỊ KẾT QUẢ ---
    if st.session_state.current_data:
        data = st.session_state.current_data
        st.markdown("---")
        st.markdown(f'<div class="check-box">{data.get("verification", "Không có dữ liệu")}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH TƯ DUY")
        for i, q in enumerate(data.get("questions", [])):
            st.write(f"**Câu {i+1}: {q.get('q')}**")
            ans = st.radio("Chọn đáp án:", q.get('options', []), index=None, key=f"quiz_{i}")
            
            correct_ans = q.get('correct', "")
            if ans and correct_ans:
                if ans.startswith(correct_ans[0]):
                    st.success("✅ Chính xác!")
                    if f"quiz_{i}" not in st.session_state.answered_status:
                        st.session_state.score += 10
                        st.session_state.answered_status[f"quiz_{i}"] = True
                        st.rerun()
                else:
                    st.error(f"❌ Sai rồi! Đáp án là: {correct_ans}")
