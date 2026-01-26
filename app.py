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

# --- 2. 高级感 CSS (玻璃拟态 & 深度动效) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Noto+Sans+SC:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans SC', sans-serif; }
    
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 玻璃拟态卡片 */
    .stInfo {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        color: #1e293b;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }

    /* 渐变按钮 */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
        color: white;
        border: none;
        height: 50px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
    }

    /* 标题动效 */
    .title-text {
        background: linear-gradient(90deg, #0f172a, #2563eb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    /* 选项卡样式自定义 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        font-weight: 600;
        font-size: 1rem;
    }

    /* 全局淡入 */
    .element-container { animation: fadeIn 0.8s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心逻辑模块 ---

def extract_text_from_pdf(file):
    try:
        stream = file.read()
        doc = fitz.open(stream=stream, filetype="pdf")
        return "".join([page.get_text() for page in doc])
    except:
        return None

def generate_academic_news_cn(client, content):
    """生成：科学网/知乎/公众号风格的长文"""
    system_prompt = (
        "你是一名顶尖的学术新闻编辑，擅长为《Phenomics》期刊撰写深度报道。"
        "请基于提供的论文内容，严格按照以下结构生成中文报道（要求专业、权威、具有吸引力）：\n"
        "1. 标题：Phenomics | [主要PI姓名]团队开发[简短技术/研究名称]\n"
        "2. 文章速递：近日，[机构]的[PI姓名]团队在《Phenomics》发表题为“[英文标题]”的研究论文。\n"
        "3. 研究背景：阐述该领域痛点及本研究的重要性。\n"
        "4. 研究方法：简述实验设计与核心技术框架。\n"
        "5. 研究结果：列出关键实验数据与结论。\n"
        "6. 研究意义：该研究的临床/科学价值及推广前景。\n"
        "7. Abstract：保留原文的核心摘要。\n"
        "8. 作者简介：提取通讯作者与第一作者信息。"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": content}],
        temperature=0.5
    )
    return response.choices[0].message.content

def generate_social_post_en(client, content, platform):
    """生成：LinkedIn/Facebook/X 风格的短文"""
    handles = {"LinkedIn": "@phenomics-journal", "Facebook": "@Journal Phenomics", "X (Twitter)": "@Phenomics_J"}
    
    system_instruction = (
        "You are a professional social media manager for 'Phenomics'. "
        "Strictly follow this visual format:\n\n"
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
    
    spec = "For X/Twitter, use 10+ hashtags. For others, use 3-5." if platform == "X (Twitter)" else ""
    prompt = f"Content: {content[:7000]}\nPlatform: {platform}\nHandle: {handles[platform]}\nRequirement: {spec}"
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# --- 4. UI 界面布局 ---

with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.divider()
    st.caption("Core Version: 5.0")
    st.caption("Style: Academic/Social Hybrid")

st.markdown('<p class="title-text">Phenomics Portal</p>', unsafe_allow_html=True)
st.markdown("##### Phenomics 期刊全渠道成果发布系统")

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown("#### 📄 论文输入")
    uploaded_file = st.file_uploader("上传 PDF 原文", type="pdf", label_visibility="collapsed")
    manual_input = st.text_area("或在此粘贴内容摘要:", height=200)
    
    st.markdown("#### 🚀 生成选项")
    do_cn = st.checkbox("生成中文深度报道 (公众号/科学网风格)", value=True)
    do_en = st.checkbox("生成英文社群推文 (LinkedIn/FB/X)", value=True)
    
    generate_btn = st.button("一键全渠道同步生成")

with col_right:
    if generate_btn:
        if not api_key:
            st.error("请先在侧边栏配置 API Key")
        else:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            source_text = extract_text_from_pdf(uploaded_file) if uploaded_file else manual_input
            
            if not source_text:
                st.warning("请上传 PDF 或输入文字内容。")
            else:
                with st.status("正在进行多模态内容编排...", expanded=True) as status:
                    # 中文生成
                    if do_cn:
                        st.write("撰写中文深度报道...")
                        cn_result = generate_academic_news_cn(client, source_text)
                        st.session_state.cn_result = cn_result
                    
                    # 英文生成
                    if do_en:
                        st.session_state.en_results = {}
                        for p in ["LinkedIn", "Facebook", "X (Twitter)"]:
                            st.write(f"正在同步 {p} 副本...")
                            st.session_state.en_results[p] = generate_social_post_en(client, source_text, p)
                    
                    status.update(label="✨ 内容全部生成完毕!", state="complete", expanded=False)

                # 展示结果
                tab_list = []
                if do_cn: tab_list.append("🇨🇳 中文深度报道")
                if do_en: tab_list.extend(["🔗 LinkedIn", "👥 Facebook", "🐦 X (Twitter)"])
                
                tabs = st.tabs(tab_list)
                
                idx = 0
                if do_cn:
                    with tabs[idx]:
                        st.markdown("##### 微信公众号/科学网/知乎 专用排版")
                        st.info(st.session_state.cn_result)
                        st.download_button("下载中文稿件", st.session_state.cn_result, file_name="CN_Press_Release.txt")
                    idx += 1
                
                if do_en:
                    for platform in ["LinkedIn", "Facebook", "X (Twitter)"]:
                        with tabs[idx]:
                            st.markdown(f"##### {platform} 推广副本")
                            st.code(st.session_state.en_results[platform], language="markdown")
                            idx += 1
    else:
        st.info("系统就绪。请上传 PDF 论文原文，系统将自动提取 PI 姓名、研究背景及核心数据并完成全渠道排版。")

st.markdown("---")
st.markdown('<p style="text-align: center; color: #64748b; font-size: 0.8rem;">Phenomics Intelligence System v5.0 | Multi-Channel Academic Publisher</p>', unsafe_allow_html=True)
