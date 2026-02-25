import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json

# --- 1. CẤU HÌNH AI THÔNG MINH (FIX LỖI 404) ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "AIzaSyCT2wrDqYloD2ZyhR3ZYvCkaYTsfM1t_ew"

genai.configure(api_key=API_KEY)

@st.cache_resource
def get_available_model():
    """Hàm tự động dò tìm model khả dụng để tránh lỗi 404"""
    try:
        # Danh sách các model ưu tiên từ cao xuống thấp
        priority_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        for target in priority_models:
            for available in models:
                if target in available:
                    return genai.GenerativeModel(available)
        return genai.GenerativeModel(models[0])
    except Exception as e:
        st.error(f"Không thể kết nối AI: {e}")
        return None

model = get_available_model()

# --- 2. QUẢN LÝ DỮ LIỆU ---
keys = {
    'score': 0, 'streak': 0, 'student_name': "", 
    'current_data': None, 'answered_status': {}, 
    'notes': "", 'manual_mode': False, 
    'history': []
}
for k, v in keys.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 3. GIAO DIỆN CSS (GIỮ NGUYÊN 70PX, 750PX, STREAK KHỦNG) ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide", page_icon="🛡️")
st.markdown(f"""
<style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    h1 {{ font-size: 70px !important; font-weight: 900 !important; color: #58a6ff !important; text-align: center; line-height: 1.1; }}
    .streak-val {{ color: #ff4b4b !important; font-size: 80px !important; font-weight: 900 !important; margin: 0; line-height: 1; text-align: center; }}
    .note-box textarea {{ height: 750px !important; background-color: #161b22 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; font-size: 16px !important; }}
    .check-box {{ background-color: #161b22; border-left: 15px solid #0056b3; padding: 35px; border-radius: 15px; border: 1px solid #30363d; line-height: 1.8; }}
    [data-testid="stSidebar"] {{ background-color: #0d1117 !important; border-right: 1px solid #30363d; }}
</style>
""", unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ (SỬA LOGIC CHUNG) ---
def process_analysis(text, title="Bài học mới"):
    if not text or model is None: 
        st.error("Dữ liệu trống hoặc AI chưa sẵn sàng.")
        return
    with st.spinner("AI đang mổ xẻ tri thức..."):
        try:
            # Gửi Prompt và ép kiểu JSON
            prompt = f"Phân tích tiếng Việt chuyên sâu (Xác thực, Phản biên, Mở rộng) + 5 câu hỏi trắc nghiệm. Trả về định dạng JSON thuần túy có key 'verification' (HTML) và 'questions': {text[:4500]}"
            res = model.generate_content(prompt)
            
            # Làm sạch dữ liệu trả về để tránh lỗi JSON
            json_match = re.search(r"\{.*\}", res.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                st.session_state.current_data = data
                st.session_state.history.append({"title": title[:30], "data": data})
                st.session_state.manual_mode = False
                st.session_state.answered_status = {}
                st.rerun()
            else:
                st.error("AI không trả về đúng định dạng. Hãy thử lại.")
        except Exception as e:
            st.error(f"Lỗi phân tích: {e}")

# --- 5. SIDEBAR (PROFILE, ĐIỂM, LỊCH SỬ) ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 40px !important;'>🛡️ SMARTLENS</h1>", unsafe_allow_html=True)
    if not st.session_state.student_name:
        name = st.text_input("👤 Tên học sinh:", key="name_reg")
        if name: st.session_state.student_name = name; st.rerun()
    else:
        st.markdown(f"### Học sinh: **{st.session_state.student_name}**")

    st.markdown(f"""
        <div style="text-align: center; background: #161b22; padding: 25px; border-radius: 15px; border: 2px solid #0056b3; margin-top: 10px;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">ĐIỂM TÍCH LŨY</p>
            <h1 style="color: #f2cc60; font-size: 70px !important; margin: 0;">{st.session_state.score}</h1>
            <hr style="border: 0.5px solid #30363d;">
            <p style="color: #8b949e; font-size: 14px; font-weight: bold;">CHUỖI (STREAK)</p>
            <p class="streak-val">{st.session_state.streak} 🔥</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("➕ BÀI HỌC MỚI", use_container_width=True, type="primary"):
        st.session_state.current_data = None
        st.session_state.manual_mode = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 📚 BÀI HỌC ĐÃ LƯU")
    for i, item in enumerate(st.session_state.history):
        if st.button(f"📖 {item['title']}", key=f"h_{i}", use_container_width=True):
            st.session_state.current_data = item['data']
            st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ THẨM ĐỊNH CHUYÊN SÂU</h1>", unsafe_allow_html=True)
m_col, n_col = st.columns([3.8, 1.2])

with n_col:
    st.markdown("### 📝 GHI CHÚ PHẢN BIỆN")
    st.session_state.notes = st.text_area("", value=st.session_state.notes, key="note_v17", height=750)

with m_col:
    t1, t2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])
    
    with t1:
        url = st.text_input("Dán link YouTube:", placeholder="https://youtube.com/...")
        if st.button("🚀 PHÂN TÍCH VIDEO", type="primary"):
            v_id = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_id:
                try:
                    ts = YouTubeTranscriptApi.get_transcript(v_id.group(1), languages=['vi', 'en'])
                    process_analysis(" ".join([i['text'] for i in ts]), title=f"Video: {v_id.group(1)}")
                except:
                    st.session_state.manual_mode = True
                    st.error("⚠️ YouTube chặn lấy phụ đề tự động.")

        if st.session_state.manual_mode:
            st.warning("👉 CÁCH DỰ PHÒNG: Lấy văn bản từ DownSub rồi dán vào đây.")
            st.link_button("1. NHẤN LẤY VĂN BẢN", f"https://downsub.com/?url={url}")
            manual_text = st.text_area("2. Dán nội dung vào đây:", height=150)
            if st.button("🔍 XÁC NHẬN PHÂN TÍCH"):
                process_analysis(manual_text, title="Video (Thủ công)")

    with t2:
        input_txt = st.text_area("Dán văn bản cần mổ xẻ:", height=300)
        if st.button("🔍 KIỂM CHỨNG NGAY", type="primary"):
            process_analysis(input_txt, title=input_txt[:20])

    # HIỂN THỊ KẾT QUẢ
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("---")
        st.markdown(f'<div class="check-box">{d.get("verification", "")}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH TƯ DUY")
        for i, q in enumerate(d.get('questions', [])):
            st.write(f"**Câu {i+1}: {q['q']}**")
            ans = st.radio("Chọn:", q['options'], index=None, key=f"q_v17_{i}")
            if ans and ans.startswith(q['correct']):
                if f"q_v17_{i}" not in st.session_state.answered_status:
                    st.session_state.score += 10
                    st.session_state.streak += 1
                    st.session_state.answered_status[f"q_v17_{i}"] = True
                    st.rerun()
                st.success("Chính xác! +10 điểm")
