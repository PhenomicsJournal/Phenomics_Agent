import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import io

# --- 1. 页面配置 ---
st.set_page_config(page_title="Phenomics 成果社群发布系统", layout="wide", initial_sidebar_state="collapsed")

# 自定义样式
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    .reportview-container .main .block-container{padding-top: 2rem;}
    footer {visibility: hidden;}
    .stInfo { background-color: #ffffff; border: 1px solid #e6e9ef; border-radius: 10px; padding: 20px; color: #1d1d1d; font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = {}

# --- 2. 配置管理 ---
with st.sidebar:
    st.title("⚙️ 配置中心")
    api_key = st.secrets.get("DEEPSEEK_API_KEY") or st.text_input("DeepSeek API Key", type="password")
    st.markdown("---")
    st.caption("版本: 4.0 | Phenomics 官方社群风格版")

client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# --- 3. 核心功能 ---

def extract_text_from_pdf(file):
    try:
        stream = file.read()
        doc = fitz.open(stream=stream, filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        file.seek(0) 
        return text
    except Exception as e:
        st.error(f"PDF 解析失败: {e}")
        return None

def generate_social_post(content, platform):
    if not client: return "请先配置 API Key"
    
    # 深度定制的 System Prompt，模仿图片中的视觉格式
    system_instruction = (
        "You are a professional social media manager for the academic journal 'Phenomics'. "
        "Your task is to create a high-impact promotional post in English. "
        "Strictly follow this visual format and do not include any other text:\n\n"
        "🚨 New Research on #[Topic]! 🧬\n\n"
        "[1 sentence summarizing the groundbreaking nature of the study] 🌍 🔬\n\n"
        "Key Insights:\n"
        "✅ [Insight 1 with #[Hashtag]] 🌿\n"
        "✅ [Insight 2 with #[Hashtag]] ⚡\n"
        "✅ [Insight 3 with #[Hashtag]] 🧠\n"
        "✅ [Insight 4 with #[Hashtag]] 🔬\n\n"
        "Published by: [Main Author Name]\n"
        "📅 Published on: [Month Day, Year]\n"
        "📄 Full Study: [DOI URL or DOI string]\n"
    )
    
    # 针对不同平台的微调要求
    platform_spec = {
        "LinkedIn": "Tone: Professional and networking-oriented. Use industry-standard hashtags.",
        "Facebook": "Tone: Engaging and community-focused. Use slightly more emojis.",
        "X (Twitter)": "Tone: Concise and catchy. Maximize hashtag usage for searchability."
    }
    
    prompt = f"Content Source: {content[:10000]}\nPlatform: {platform}\nSpecific Requirement: {platform_spec.get(platform)}\n\n" \
             f"Instruction: Extract the Author, Publication Date, and DOI from the text. " \
             f"If specific metadata is missing, use placeholders like [Author Name] or [DOI]."

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"生成失败: {str(e)}"

# --- 4. 界面布局 ---

st.title("🧬 Phenomics 官方社群文案生成器")
st.markdown("自动生成符合 **LinkedIn, Facebook, X** 风格的标准化推文。")

col_in, col_out = st.columns([1, 1.5], gap="large")

with col_in:
    st.subheader("📄 上传论文")
    source_pdf = st.file_uploader("上传 PDF 原文", type="pdf")

    st.markdown("### 📢 默认渠道")
    # 默认勾选图片中的三个平台
    target_platforms = ["LinkedIn", "Facebook", "X (Twitter)"]
    targets = st.multiselect("确认生成平台", target_platforms, default=target_platforms)
    
    generate_btn = st.button("🚀 一键生成标准化推文", use_container_width=True)

with col_out:
    st.subheader("📱 推文预览")
    
    if generate_btn and source_pdf:
        with st.spinner("正在提取数据并排版..."):
            raw_text = extract_text_from_pdf(source_pdf)
            if raw_text:
                st.session_state.results = {} 
                for platform in targets:
                    st.session_state.results[platform] = generate_social_post(raw_text, platform)
            else:
                st.error("未能解析 PDF 文本。")

    if st.session_state.results:
        # 汇总用于下载的文本
        download_text = ""
        for platform, copy in st.session_state.results.items():
            st.markdown(f"**{platform} Post Preview:**")
            st.info(copy)
            download_text += f"=== {platform} ===\n\n{copy}\n\n"
        
        st.download_button(
            "📥 下载全渠道文案 (.txt)",
            data=download_text,
            file_name="Phenomics_Social_Posts.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("文案将严格按照图片格式生成，包含 ✅、#标签 和 DOI 信息。")
