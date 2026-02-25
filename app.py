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

# --- 2. QUẢN LÝ DỮ LIỆU ---
keys = ['score', 'streak', 'student_name', 'current_data', 'answered_status', 'notes', 'manual_mode']
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = 0 if k in ['score', 'streak'] else (False if k == 'manual_mode' else ({} if k == 'answered_status' else ""))

# --- 3. GIAO DIỆN (PHÓNG TO CHỮ STREAK & NOTE 750PX) ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide", page_icon="🛡️")

st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #58a6ff !important; text-align: center; }}
    /* PHÓNG TO CHỮ STREAK */
    .streak-val {{ color: #ff4b4b !important; font-size: 80px !important; font-weight: 900 !important; margin: 0; line-height: 1; }}
    .note-box textarea {{ height: 750px !important; background-color: #161b22 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; }}
    .check-box {{ background-color: #161b22; border-left: 15px solid #0056b3; padding: 35px; border-radius: 15px; }}
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (PROFILE & ĐIỂM SỐ) ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 40px !important;'>🛡️ SMARTLENS</h1>", unsafe_allow_html=True)
    if not st.session_state.student_name:
        name = st.text_input("👤 Nhập tên học sinh:", key="name_input")
        if name: st.session_state.student_name = name; st.rerun()
    else:
        st.markdown(f"### Học sinh: **{st.session_state.student_name}**")

    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 20px; border-radius: 15px; border: 2px solid #0056b3;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 70px !important; margin: 0;">{st.session_state.score}</h1>
            <hr style="border: 0.5px solid #30363d;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">CHUỖI (STREAK)</p>
            <p class="streak-val">{st.session_state.streak} 🔥</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)
m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("### 📝 GHI CHÚ PHẢN BIỆN")
    st.markdown('<div class="note-box">', unsafe_allow_html=True)
    st.session_state.notes = st.text_area("", value=st.session_state.notes, key="note_final", placeholder="Ghi lại ý tưởng...")
    st.markdown('</div>', unsafe_allow_html=True)

with m_col:
    t1, t2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])
    
    with t1:
        url = st.text_input("Dán link YouTube tại đây:", key="yt_url")
        
        # Nút Phân tích chính
        if st.button("🚀 BẮT ĐẦU PHÂN TÍCH", type="primary"):
            v_id = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_id:
                with st.spinner("Hệ thống đang tự động trích xuất phụ đề..."):
                    try:
                        ts = YouTubeTranscriptApi.get_transcript(v_id.group(1), languages=['vi', 'en'])
                        text = " ".join([i['text'] for i in ts])
                        # Nếu thành công, gửi AI luôn
                        res = model.generate_content(f"Phân tích tiếng Việt + JSON: {text[:5000]}")
                        st.session_state.current_data = json.loads(re.search(r"\{.*\}", res.text, re.DOTALL).group())
                        st.session_state.manual_mode = False
                        st.rerun()
                    except:
                        # Nếu thất bại, bật chế độ thủ công
                        st.session_state.manual_mode = True
                        st.error("⚠️ YouTube không cho phép lấy phụ đề tự động. Hãy dùng 'Cách dự phòng' hiện ra bên dưới.")

        # CHỈ HIỆN KHI BỊ LỖI PHỤ ĐỀ
        if st.session_state.manual_mode:
            st.markdown("""<div style="background:#21262d; padding:20px; border-radius:10px; border:1px solid #f2cc60;">
                <h3 style="color:#f2cc60; margin:0;">🛠️ CÁCH DỰ PHÒNG (DÀNH CHO GIÁM KHẢO)</h3>
                <p>Vì video này bị chặn, thầy cô vui lòng làm nhanh 2 bước:</p>
            </div>""", unsafe_allow_html=True)
            
            st.link_button("👉 BƯỚC 1: NHẤN ĐỂ LẤY VĂN BẢN VIDEO", f"https://downsub.com/?url={url}")
            
            manual_text = st.text_area("👉 BƯỚC 2: Dán nội dung vừa lấy được vào đây:", height=150)
            if st.button("🔍 TIẾP TỤC THẨM ĐỊNH"):
                if manual_text:
                    with st.spinner("AI đang xử lý..."):
                        res = model.generate_content(f"Phân tích tiếng Việt + JSON: {manual_text[:5000]}")
                        st.session_state.current_data = json.loads(re.search(r"\{.*\}", res.text, re.DOTALL).group())
                        st.session_state.manual_mode = False
                        st.rerun()

    with t2:
        direct_txt = st.text_area("Dán văn bản bất kỳ:", height=300)
        if st.button("🔍 KIỂM CHỨNG NGAY"):
             # Logic xử lý AI văn bản...
             pass

    # HIỂN THỊ KẾT QUẢ
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("---")
        st.markdown(f'<div class="check-box">{d["verification"]}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH TƯ DUY")
        for i, q in enumerate(d['questions']):
            st.write(f"**Câu {i+1}: {q['q']}**")
            ans = st.radio("Chọn:", q['options'], index=None, key=f"q_{i}")
            if ans and ans.startswith(q['correct']):
                if f"q_{i}" not in st.session_state.answered_status:
                    st.session_state.score += 10
                    st.session_state.streak += 1
                    st.session_state.answered_status[f"q_{i}"] = True
                    st.rerun()
                st.success("✅ Chính xác!")
