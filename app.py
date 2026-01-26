import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import time

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Phenomics AI Portal",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. 高级高级感 CSS 定制 ---
st.markdown("""
    <style>
    /* 全局字体与背景 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 玻璃拟态卡片 */
    .stInfo {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        padding: 25px;
        transition: transform 0.3s ease;
    }
    
    /* 按钮高级动画 */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
    }
    
    /* 标题动效 */
    .main-title {
        background: linear-gradient(90deg, #1e3a8a, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    /* 淡入动画 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .element-container { animation: fadeIn 0.5s ease-out; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心后端逻辑 ---
def extract_text_from_pdf(file):
    try:
        stream = file.read()
        doc = fitz.open(stream=stream, filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        return text
    except Exception as e:
        st.error(f"PDF Parsing Error: {e}")
        return None

def generate_social_post(client, content, platform):
    # 账号配置
    handles = {
        "LinkedIn": "@phenomics-journal",
        "Facebook": "@Journal Phenomics",
        "X (Twitter)": "@Phenomics_J"
    }
    
    # 平台特征描述
    specs = {
        "LinkedIn": "Professional, networking-focused, highly structured. (3-5 tags)",
        "Facebook": "Community-focused, engaging, slightly more emojis. (3-5 tags)",
        "X (Twitter)": "Concise, viral, aggressive hashtag usage (at least 10 relevant tags) for maximum reach."
    }

    system_instruction = (
        "You are the Lead Editor for 'Phenomics' Social Media. "
        "Strictly produce high-quality posts in this visual format:\n\n"
        "🚨 New Research on #[Topic]! 🧬\n\n"
        "[Punchy 1-sentence summary] 🌍 🔬\n\n"
        "Key Insights:\n"
        "✅ [Insight 1 with #[Tag]] 🌿\n"
        "✅ [Insight 2 with #[Tag]] ⚡\n"
        "✅ [Insight 3 with #[Tag]] 🧠\n"
        "✅ [Insight 4 with #[Tag]] 🔬\n\n"
        "Published by: [Author Name]\n"
        "📅 Published on: [Date]\n"
        "📄 Full Study: [DOI URL]\n\n"
        "Connect with us: [Handle]"
    )

    prompt = (
        f"Context: {content[:8000]}\n\n"
        f"Platform: {platform}\n"
        f"Handle: {handles[platform]}\n"
        f"Style: {specs[platform]}\n"
        f"Task: Identify author, date, and DOI accurately. Use emojis and maintain the structure."
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Generation failed: {str(e)}"

# --- 4. UI 布局 ---

# 侧边栏配置
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/dna-helix.png", width=60)
    st.markdown("### Control Center")
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.divider()
    st.caption("System Version: 5.0")
    st.caption("Engine: DeepSeek-V3")

# 主界面
st.markdown('<p class="main-title">Phenomics Portal</p>', unsafe_allow_html=True)
st.markdown("##### Research Dissemination System")

c1, c2 = st.columns([1, 1.4], gap="large")

with c1:
    st.markdown("#### 📄 Content Source")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    manual_text = st.text_area("Or paste abstract below:", height=150, placeholder="Paste research text here...")
    
    st.markdown("#### 📢 Target Platforms")
    selected_platforms = st.multiselect(
        "Select distribution channels",
        ["LinkedIn", "Facebook", "X (Twitter)"],
        default=["LinkedIn", "Facebook", "X (Twitter)"]
    )
    
    generate_btn = st.button("Generate Synchronized Content")

with c2:
    st.markdown("#### 📱 Multi-Channel Preview")
    
    if generate_btn:
        if not api_key:
            st.warning("Please enter API Key in the sidebar.")
        else:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            # 文本提取逻辑
            content = ""
            if uploaded_file:
                content = extract_text_from_pdf(uploaded_file)
            else:
                content = manual_text
            
            if content:
                results = {}
                with st.status("🚀 Processing Research Intelligence...", expanded=True) as status:
                    for p in selected_platforms:
                        st.write(f"Crafting {p} copy...")
                        results[p] = generate_social_post(client, content, p)
                    status.update(label="✨ Content Synthesized!", state="complete", expanded=False)
                
                # 使用 Tabs 展示预览，极其高级
                tabs = st.tabs(selected_platforms)
                full_download = ""
                for i, p in enumerate(selected_platforms):
                    with tabs[i]:
                        st.markdown(f"**{p} Content Preview**")
                        st.info(results[p])
                        full_download += f"--- {p} ---\n{results[p]}\n\n"
                
                st.download_button(
                    label="📥 Download All Assets",
                    data=full_download,
                    file_name="Phenomics_Social_Pack.txt",
                    mime="text/plain"
                )
            else:
                st.error("No source content detected.")
    else:
        # 初始占位图
        st.info("Upload a paper to see the AI-generated social media strategy.")

# 底部点缀
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #94a3b8; font-size: 0.8rem;">'
    'Phenomics AI Distribution Hub | Version 5.0 | High-Fidelity Output'
    '</p>', 
    unsafe_allow_html=True
)
