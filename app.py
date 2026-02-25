import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json

# --- 1. CẤU HÌNH AI ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "AIzaSyCT2wrDqYloD2ZyhR3ZYvCkaYTsfM1t_ew"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. QUẢN LÝ DỮ LIỆU (THÊM PHẦN LỊCH SỬ) ---
keys = {
    'score': 0, 'streak': 0, 'student_name': "", 
    'current_data': None, 'answered_status': {}, 
    'notes': "", 'manual_mode': False, 
    'history': [] # Nơi lưu lại các bài học cũ
}
for k, v in keys.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 3. CSS GIAO DIỆN ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide", page_icon="🛡️")
st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #58a6ff !important; text-align: center; }}
    .streak-val {{ color: #ff4b4b !important; font-size: 80px !important; font-weight: 900 !important; margin: 0; line-height: 1; }}
    .note-box textarea {{ height: 750px !important; background-color: #161b22 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; }}
    .check-box {{ background-color: #161b22; border-left: 15px solid #0056b3; padding: 35px; border-radius: 15px; border: 1px solid #30363d; }}
    .history-item {{ padding: 10px; border-bottom: 1px solid #30363d; cursor: pointer; color: #58a6ff; }}
</style>
""", unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ CHUNG ---
def process_analysis(text, title="Bài học mới"):
    if not text: return
    with st.spinner("AI đang thẩm định chuyên sâu..."):
        try:
            res = model.generate_content(f"Phân tích tiếng Việt (Xác thực, Phản biện, Mở rộng) + 5 câu hỏi trắc nghiệm JSON: {text[:5000]}")
            data = json.loads(re.search(r"\{.*\}", res.text, re.DOTALL).group())
            st.session_state.current_data = data
            # Lưu vào lịch sử
            st.session_state.history.append({"title": title[:30] + "...", "data": data})
            st.session_state.manual_mode = False
            st.session_state.answered_status = {}
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi AI: {e}")

# --- 5. SIDEBAR (PROFILE, ĐIỂM & LỊCH SỬ) ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 40px !important;'>🛡️ SMARTLENS</h1>", unsafe_allow_html=True)
    if not st.session_state.student_name:
        name = st.text_input("👤 Tên học sinh:", key="name_in")
        if name: st.session_state.student_name = name; st.rerun()
    else:
        st.markdown(f"### Học sinh: **{st.session_state.student_name}**")

    # Điểm & Streak
    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 20px; border-radius: 15px; border: 2px solid #0056b3;">
            <p style="color: #8b949e; font-size: 12px; font-weight: bold;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 60px !important; margin: 0;">{st.session_state.score}</h1>
            <hr style="border: 0.5px solid #30363d;">
            <p style="color: #8b949e; font-size: 12px; font-weight: bold;">CHUỖI (STREAK)</p>
            <p class="streak-val">{st.session_state.streak} 🔥</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("➕ BÀI HỌC MỚI", use_container_width=True, type="primary"):
        st.session_state.current_data = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 📚 LỊCH SỬ BÀI HỌC")
    for i, item in enumerate(st.session_state.history):
        if st.button(f"📖 {item['title']}", key=f"hist_{i}", use_container_width=True):
            st.session_state.current_data = item['data']
            st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)
m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("### 📝 GHI CHÚ PHẢN BIỆN")
    st.session_state.notes = st.text_area("", value=st.session_state.notes, key="note_v16", height=750)

with m_col:
    t1, t2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])
    
    with t1:
        url = st.text_input("Dán link YouTube tại đây:", key="yt_url_v16")
        if st.button("🚀 PHÂN TÍCH VIDEO", type="primary"):
            v_id = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_id:
                try:
                    ts = YouTubeTranscriptApi.get_transcript(v_id.group(1), languages=['vi', 'en'])
                    full_txt = " ".join([i['text'] for i in ts])
                    process_analysis(full_txt, title=f"Video: {v_id.group(1)}")
                except:
                    st.session_state.manual_mode = True
                    st.error("⚠️ Không thể lấy phụ đề tự động.")

        if st.session_state.manual_mode:
            st.info("Cách dự phòng: Nhấn nút lấy văn bản rồi dán vào ô dưới.")
            st.link_button("👉 LẤY VĂN BẢN TẠI DOWNSUB", f"https://downsub.com/?url={url}")
            manual_text = st.text_area("Dán nội dung văn bản vào đây:", height=150)
            if st.button("🔍 XÁC NHẬN VĂN BẢN"):
                process_analysis(manual_text, title="Video (Thủ công)")

    with t2:
        input_txt = st.text_area("Dán văn bản bài báo/kiến thức cần mổ xẻ:", height=300)
        if st.button("🔍 KIỂM CHỨNG NGAY", type="primary"):
            if input_txt:
                process_analysis(input_txt, title=input_txt[:20])

    # HIỂN THỊ KẾT QUẢ
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("---")
        st.markdown(f'<div class="check-box">{d["verification"]}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH TƯ DUY")
        for i, q in enumerate(d['questions']):
            st.write(f"**Câu {i+1}: {q['q']}**")
            ans = st.radio("Chọn đáp án:", q['options'], index=None, key=f"q_v16_{i}")
            if ans and ans.startswith(q['correct']):
                if f"q_v16_{i}" not in st.session_state.answered_status:
                    st.session_state.score += 10
                    st.session_state.streak += 1
                    st.session_state.answered_status[f"q_v16_{i}"] = True
                    st.rerun()
                st.success("✅ Chính xác! +10 điểm")
