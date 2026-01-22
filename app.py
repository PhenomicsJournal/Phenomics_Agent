import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import io

# --- 1. 页面配置 ---
st.set_page_config(page_title="Phenomics 科研成果发布系统", layout="wide", initial_sidebar_state="collapsed")

# 自定义样式
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    .reportview-container .main .block-container{padding-top: 2rem;}
    footer {visibility: hidden;}
    .stInfo { background-color: #f0f2f6; border-left: 5px solid #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 持久化存储 ---
if "results" not in st.session_state:
    st.session_state.results = {}

# --- 3. 侧边栏配置 ---
with st.sidebar:
    st.title("⚙️ 配置中心")
    # 部署到云端时，建议留空让用户输入，或者使用 Secrets
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.markdown("---")
    st.caption("版本: 3.0 | 模式: 纯PDF定稿版")

client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


# --- 4. 核心处理模块 ---

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


def generate_final_copy(content, platform, style_guide):
    if not client: return "请先配置 API Key"

    system_instruction = (
        "你是一位顶尖的科学传播官。你的输出直接用于公开发布。\n"
        "直接输出文案内容，禁止任何开场白、确认语或结尾客套话。\n"
        "只输出文案本身（包括标题和正文）。"
    )

    prompt = f"内容：{content[:10000]}\n平台：{platform}\n要求：{style_guide}"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"生成失败: {str(e)}"


# --- 5. 界面布局 ---

st.title("🧪 Phenomics 科研成果发布系统")
st.markdown("请上传论文 PDF，系统将自动提炼并生成多平台宣传文本。")
st.markdown("---")

col_in, col_out = st.columns([1, 1.5], gap="large")

with col_in:
    st.subheader("📄 上传内容源")
    source_pdf = st.file_uploader("上传论文原文 (PDF)", type="pdf")

    st.markdown("### 📢 发布渠道选择")
    PLATFORMS = {
        "小红书": "标题党，多Emoji，语气活泼，含5个热门标签。",
        "LinkedIn": "商务专业风格，强调行业前瞻性与技术逻辑。",
        "Twitter/X": "短小精悍，以一句话震撼结论开头。",
        "微信朋友圈": "真诚分享语气，适合同行和朋友点赞，简洁有力。"
    }
    targets = st.multiselect("选择生成渠道", list(PLATFORMS.keys()), default=["小红书", "LinkedIn"])

    generate_btn = st.button("🚀 开始生成定稿", use_container_width=True)

with col_out:
    st.subheader("✨ 渠道定稿预览")

    if generate_btn and source_pdf:
        with st.spinner("正在研读文档并创作..."):
            raw_text = extract_text_from_pdf(source_pdf)
            if raw_text:
                st.session_state.results = {}  # 重置旧结果
                for platform in targets:
                    st.session_state.results[platform] = generate_final_copy(raw_text, platform, PLATFORMS[platform])
            else:
                st.error("未能从 PDF 中提取出有效文本。")

    if st.session_state.results:
        all_text = ""
        for platform, copy in st.session_state.results.items():
            st.markdown(f"#### 【{platform}频道】")
            st.info(copy)
            all_text += f"### {platform}\n{copy}\n\n---\n\n"

        st.download_button(
            "📥 下载全渠道定稿 (.md)",
            data=all_text,
            file_name="成果发布定稿汇总.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.info("生成的文案将在此处显示")