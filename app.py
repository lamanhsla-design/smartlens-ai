import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json

# --- 1. CẤU HÌNH AI ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    # Key này chỉ dùng để bạn chạy thử trên máy tính cá nhân
    API_KEY = "AIzaSyCT2wrDqYloD2ZyhR3ZYvCkaYTsfM1t_ew"

genai.configure(api_key=API_KEY)
@st.cache_resource
def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for p in priority:
            if p in available_models: return genai.GenerativeModel(p)
        return genai.GenerativeModel(available_models[0])
    except: return None

model = get_working_model()

# --- 2. QUẢN LÝ SESSION ---
keys = ['score', 'streak', 'student_name', 'current_data', 'answered_status', 'notes', 'last_input']
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = 0 if k in ['score', 'streak'] else ({} if k == 'answered_status' else "")

# --- 3. SIDEBAR (GIAO DIỆN) ---
st.set_page_config(page_title="SmartLens Pro", layout="wide", page_icon="🛡️")

with st.sidebar:
    st.markdown("<h1 style='color: white; font-size: 45px; margin-bottom: 0;'>🛡️ SMARTLENS</h1>", unsafe_allow_html=True)
    
    if not st.session_state.student_name:
        name = st.text_input("👤 Tên học sinh (Nhấn Enter):", key="st_name_v11")
        if name:
            st.session_state.student_name = name
            st.rerun()
    else:
        st.markdown(f"<p style='color: white; font-size: 22px;'>Chào học sinh: <b style='color:#58a6ff;'>{st.session_state.student_name}</b></p>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 25px; border-radius: 15px; border: 2px solid #0056b3;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 75px; margin: 0; line-height: 1;">{st.session_state.score}</h1>
            <hr style="border: 0.5px solid #30363d; margin: 15px 0;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">STREAK</p>
            <h2 style="color: #ff4b4b; font-size: 55px; margin: 0; line-height: 1;">{st.session_state.streak} 🔥</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    if st.button("➕ Bài học mới", type="primary", use_container_width=True):
        st.session_state.current_data = ""
        st.session_state.answered_status = {}
        st.session_state.last_input = ""
        st.rerun()

# --- 4. CSS ---
st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    html, body, [class*="st-"], p, li {{ font-size: 17px !important; }}
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #0056b3 !important; line-height: 1.1; }}
    h2 {{ font-size: 45px !important; font-weight: 700 !important; color: #58a6ff !important; }}
    .note-box textarea {{
        font-size: 14px !important; line-height: 1.5 !important;
        background-color: #0d1117 !important; color: #e6edf3 !important;
        height: 750px !important; border: 1px dashed #30363d !important;
    }}
    .check-box {{
        background-color: #161b22; color: #e6edf3 !important;
        border-left: 15px solid #0056b3; padding: 40px; border-radius: 20px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8); margin-bottom: 40px;
    }}
</style>
""", unsafe_allow_html=True)

# --- 5. HÀM PHÂN TÍCH (FIX KEYERROR) ---
def analyze_deep_stable(content):
    prompt = f"""
    Bạn là Chuyên gia Thẩm định Tri thức cao cấp. Hãy phân tích bằng TIẾNG VIỆT:
    "{content[:4000]}"
    
    Yêu cầu JSON chuẩn:
    1. "verification": Nội dung HTML (Xác thực, Phản biện, Bối cảnh).
    2. "questions": List 5 câu hỏi trắc nghiệm. Mỗi câu bắt buộc có khóa "q", "options", và "correct".
    
    Lưu ý: "correct" phải là ký tự chữ cái đáp án đúng (A, B, C hoặc D).
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(raw_text[start:end])
        return None
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return None

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)

m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("<br>"*2, unsafe_allow_html=True)
    with st.expander("📝 KHÔNG GIAN GHI CHÚ", expanded=True):
        st.markdown('<div class="note-box">', unsafe_allow_html=True)
        st.session_state.notes = st.text_area("Ghi chú tại đây...", value=st.session_state.notes, key="note_v11")
        st.markdown('</div>', unsafe_allow_html=True)

with m_col:
    t1, t2 = st.tabs(["📺 Video YouTube", "📝 Văn bản"])
    with t1:
        yt = st.text_input("Dán link YouTube:", key="yt_v11")
        if yt and st.button("🚀 PHÂN TÍCH VIDEO"):
            v_id_match = re.search(r"(?:v=|\/shorts\/|be\/)([a-zA-Z0-9_-]{11})", yt)
            if v_id_match:
                with st.spinner("Đang mổ xẻ nội dung..."):
                    try:
                        v_id = v_id_match.group(1)
                        trans = YouTubeTranscriptApi.list_transcripts(v_id)
                        try: c = trans.find_transcript(['vi']).fetch()
                        except: c = trans.find_transcript(['en']).translate('vi').fetch()
                        text = " ".join([i['text'] for i in c])
                        res = analyze_deep_stable(text)
                        if res: st.session_state.current_data = res; st.rerun()
                    except: st.error("Lỗi phụ đề!")

    with t2:
        txt = st.text_area("Dán nội dung:", value=st.session_state.last_input, height=180)
        if txt and st.button("🔍 DOUBLE CHECK"):
            st.session_state.last_input = txt
            with st.spinner("Đang đối soát..."):
                res = analyze_deep_stable(txt)
                if res: st.session_state.current_data = res; st.rerun()

    if st.session_state.current_data:
        data = st.session_state.current_data
        st.markdown("---")
        st.markdown("## 📊 KẾT QUẢ")
        st.markdown(f'<div class="check-box">{data.get("verification", "Không có dữ liệu")}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH")
        # Kiểm tra khóa 'questions' tồn tại
        questions = data.get("questions", [])
        for i, q in enumerate(questions):
            st.write(f"**Câu {i+1}: {q.get('q', 'Lỗi câu hỏi')}**")
            options = q.get('options', [])
            ans = st.radio("Chọn đáp án:", options, index=None, key=f"q_v11_{i}")
            
            # Bảo vệ bằng cách sử dụng .get() để tránh KeyError 'correct'
            correct_ans = q.get('correct', "")
            
            if ans and correct_ans:
                if ans.startswith(correct_ans[0]):
                    st.success("✅ ĐÚNG!")
                    if f"q_v11_{i}" not in st.session_state.answered_status:
                        st.session_state.score += 10
                        st.session_state.answered_status[f"q_v11_{i}"] = True
                        st.rerun()
                else:
                    st.error(f"❌ SAI! Đáp án là: {correct_ans}")
