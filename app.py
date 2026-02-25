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

# --- 2. QUẢN LÝ SESSION (ĐIỂM, STREAK, PROFILE) ---
keys = ['score', 'streak', 'student_name', 'current_data', 'answered_status', 'notes', 'show_manual']
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = 0 if k in ['score', 'streak'] else ({} if k == 'answered_status' else (False if k == 'show_manual' else ""))

# --- 3. CSS GIAO DIỆN (TIÊU ĐỀ 70PX, NOTE 750PX) ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide", page_icon="🛡️")

st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    /* TIÊU ĐỀ KHỔNG LỒ */
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #58a6ff !important; line-height: 1.1; text-align: center; }}
    h2 {{ font-size: 45px !important; color: #f2cc60 !important; }}
    
    /* Ô GHI CHÚ DIỆN TÍCH CỰC ĐẠI */
    .note-box textarea {{
        height: 750px !important; font-size: 16px !important;
        background-color: #0d1117 !important; color: #e6edf3 !important;
        border: 1px dashed #30363d !important;
    }}
    
    /* KHỐI HIỂN THỊ KẾT QUẢ */
    .check-box {{
        background-color: #161b22; border-left: 15px solid #0056b3;
        padding: 40px; border-radius: 20px; font-size: 18px; line-height: 1.8;
    }}
    
    /* SIDEBAR CÁ NHÂN HÓA */
    [data-testid="stSidebar"] {{ background-color: #0d1117; border-right: 1px solid #30363d; }}
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (PROFILE & ĐIỂM SỐ) ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 40px !important;'>🛡️ SMARTLENS</h1>", unsafe_allow_html=True)
    
    if not st.session_state.student_name:
        name = st.text_input("👤 Nhập tên để bắt đầu:", key="st_name_input")
        if name:
            st.session_state.student_name = name
            st.rerun()
    else:
        st.markdown(f"### Chào học sinh: **{st.session_state.student_name}**")

    # KHỐI ĐIỂM SỐ
    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 25px; border-radius: 15px; border: 2px solid #0056b3;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 75px !important; margin: 0;">{st.session_state.score}</h1>
            <hr style="border: 0.5px solid #30363d;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">CHUỖI HỌC TẬP</p>
            <h2 style="color: #ff4b4b; font-size: 55px !important; margin: 0;">{st.session_state.streak} 🔥</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ Bài học mới", use_container_width=True):
        st.session_state.current_data = None
        st.session_state.answered_status = {}
        st.rerun()

# --- 5. HÀM PHÂN TÍCH AI ---
def analyze_master(text):
    prompt = f"Phân tích chuyên sâu tiếng Việt (Xác thực, Phản biện, Mở rộng) + 5 câu hỏi trắc nghiệm JSON: {text[:5000]}"
    try:
        res = model.generate_content(prompt)
        match = re.search(r"\{.*\}", res.text, re.DOTALL)
        return json.loads(match.group())
    except: return None

# --- 6. GIAO DIỆN CHÍNH (CỘT CHÍNH & CỘT GHI CHÚ) ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)

m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("### 📝 GHI CHÚ PHẢN BIỆN")
    st.markdown('<div class="note-box">', unsafe_allow_html=True)
    st.session_state.notes = st.text_area("Ghi chú ý tưởng tại đây...", value=st.session_state.notes, key="note_area_final")
    st.markdown('</div>', unsafe_allow_html=True)

with m_col:
    t1, t2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])
    
    with t1:
        url = st.text_input("Dán link YouTube:", placeholder="https://youtube.com/...")
        final_text = ""
        
        if st.button("🚀 BẮT ĐẦU PHÂN TÍCH"):
            v_id_match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_id_match:
                with st.spinner("Đang trích xuất tri thức..."):
                    try:
                        ts = YouTubeTranscriptApi.get_transcript(v_id_match.group(1), languages=['vi', 'en'])
                        final_text = " ".join([i['text'] for i in ts])
                        st.session_state.show_manual = False
                    except:
                        st.error("⚠️ Không lấy được phụ đề tự động.")
                        st.session_state.show_manual = True

        if st.session_state.show_manual:
            st.warning("👉 Vui lòng dán nội dung văn bản (Transcript) của video vào đây:")
            manual_in = st.text_area("Dán văn bản tại đây...", height=150)
            if st.button("🔍 TIẾP TỤC VỚI VĂN BẢN NÀY"):
                final_text = manual_in

        if final_text:
            with st.spinner("AI đang thẩm định chuyên sâu..."):
                res = analyze_master(final_text)
                if res: 
                    st.session_state.current_data = res
                    st.rerun()

    with t2:
        txt_input = st.text_area("Dán nội dung cần kiểm chứng:", height=200)
        if st.button("🔍 KIỂM CHỨNG NGAY"):
            with st.spinner("Đang đối soát..."):
                res = analyze_master(txt_input)
                if res: 
                    st.session_state.current_data = res
                    st.rerun()

    # HIỂN THỊ KẾT QUẢ & CÂU HỎI
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("---")
        st.markdown("## 📊 KẾT QUẢ THẨM ĐỊNH")
        st.markdown(f'<div class="check-box">{d["verification"]}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH TƯ DUY")
        for i, q in enumerate(d['questions']):
            st.write(f"**Câu {i+1}: {q['q']}**")
            ans = st.radio("Chọn đáp án:", q['options'], index=None, key=f"quiz_{i}")
            if ans and ans.startswith(q['correct']):
                if f"quiz_{i}" not in st.session_state.answered_status:
                    st.session_state.score += 10
                    st.session_state.answered_status[f"quiz_{i}"] = True
                    st.rerun()
                st.success("✅ Chính xác! +10 điểm")
