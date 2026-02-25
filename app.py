import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json

# --- 1. CẤU HÌNH AI (GIỮ NGUYÊN) ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "AIzaSyCT2wrDqYloD2ZyhR3ZYvCkaYTsfM1t_ew"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. GIAO DIỆN & CSS (GIỮ NGUYÊN) ---
st.set_page_config(page_title="SmartLens AI Pro", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    h1 { font-size: 70px !important; color: #58a6ff !important; text-align: center; font-weight: 900; }
    .check-box { background-color: #161b22; border-left: 15px solid #58a6ff; padding: 35px; border-radius: 15px; margin-top: 25px; }
    .stTextArea textarea { background-color: #0d1117 !important; border: 1px dashed #30363d !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. HÀM XỬ LÝ (GIỮ NGUYÊN) ---
def analyze_content(text):
    if not text: return None
    prompt = f"Phân tích chuyên sâu tiếng Việt (Xác thực, Phản biện, Mở rộng) + 5 câu hỏi trắc nghiệm JSON: {text[:5000]}"
    try:
        res = model.generate_content(prompt)
        match = re.search(r"\{.*\}", res.text, re.DOTALL)
        return json.loads(match.group())
    except: return None

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown("<h1>🛡️ SMARTLENS PRO</h1>", unsafe_allow_html=True)

m_col, n_col = st.columns([3.5, 1.5])

with n_col:
    st.markdown("### 📝 GHI CHÚ (NOTES)")
    st.text_area("Ghi chú lại các luận điểm...", height=700)

with m_col:
    tab1, tab2 = st.tabs(["📺 KIỂM CHỨNG VIDEO", "📝 KIỂM CHỨNG VĂN BẢN"])

    with tab1:
        # THÊM: Gợi ý video để giám khảo không bị bỡ ngỡ
        st.info("📌 **Mẹo cho Giám khảo:** Hãy thử với các video có phụ đề chuẩn như bài diễn thuyết của Steve Jobs hoặc các video giáo dục từ kênh Kurzesagt.")
        
        url = st.text_input("Dán link YouTube tại đây:", placeholder="https://www.youtube.com/watch?v=...")
        
        # Biến chứa dữ liệu văn bản cuối cùng
        final_text = ""

        # NÚT PHÂN TÍCH CHÍNH
        if st.button("🚀 BẮT ĐẦU PHÂN TÍCH"):
            v_id_match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", url)
            if v_id_match:
                v_id = v_id_match.group(1)
                with st.spinner("Đang trích xuất tri thức..."):
                    try:
                        # Thử lấy tiếng Việt hoặc tiếng Anh
                        ts = YouTubeTranscriptApi.get_transcript(v_id, languages=['vi', 'en'])
                        final_text = " ".join([i['text'] for i in ts])
                    except:
                        # Nếu lỗi, không báo lỗi đỏ mà hiện hướng dẫn cứu cánh
                        st.error("⚠️ YouTube không cung cấp phụ đề tự động cho video này.")
                        st.session_state.show_manual = True # Kích hoạt ô nhập thủ công
            else:
                st.warning("Vui lòng nhập đường link YouTube hợp lệ.")

        # CƠ CHẾ CỨU CÁNH: Nếu không lấy được phụ đề, hiện ô dán văn bản ngay lập tức
        if st.session_state.get('show_manual', False):
            st.markdown("---")
            st.write("👉 **Vì chính sách bảo mật của YouTube, vui lòng dán nội dung văn bản (Transcript) của video vào ô dưới đây để tiếp tục phân tích:**")
            manual_text = st.text_area("Nội dung văn bản video:", height=150, help="Bạn có thể copy nội dung từ mô tả video hoặc các trang hỗ trợ lấy transcript.")
            if st.button("🔍 TIẾP TỤC PHÂN TÍCH"):
                final_text = manual_text

        # KHI ĐÃ CÓ VĂN BẢN (DÙ TỰ ĐỘNG HAY THỦ CÔNG)
        if final_text:
            with st.spinner("AI đang thẩm định chuyên sâu..."):
                result = analyze_content(final_text)
                if result:
                    st.session_state.data = result
                    st.session_state.show_manual = False # Ẩn ô nhập thủ công sau khi thành công
                    st.rerun()

    with tab2:
        direct_text = st.text_area("Dán đoạn văn bản cần kiểm chứng:", height=250)
        if st.button("🔍 THẨM ĐỊNH NGAY"):
            res = analyze_content(direct_text)
            if res: 
                st.session_state.data = res
                st.rerun()

    # --- 5. HIỂN THỊ KẾT QUẢ (GIỮ NGUYÊN TẤT CẢ) ---
    if "data" in st.session_state:
        d = st.session_state.data
        st.markdown("---")
        st.markdown(f'<div class="check-box">{d["verification"]}</div>', unsafe_allow_html=True)
        
        st.markdown("## ✍️ THỬ THÁCH TƯ DUY")
        for i, q in enumerate(d['questions']):
            st.write(f"**Câu {i+1}: {q['q']}**")
            ans = st.radio("Chọn đáp án:", q['options'], index=None, key=f"q_v13_{i}")
            if ans and ans.startswith(q['correct']):
                st.success("✅ Chính xác!")
