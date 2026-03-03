import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import os
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

def generate_content(client, source_text, system_prompt):
    """通用生成函数：使用指定的系统提示词和论文内容生成文本"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": source_text[:7000]}  # 截断长文本
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

# --- 4. UI 界面布局 ---

with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.divider()
    st.caption("Core Version: 5.1 (Dynamic Prompts)")
    st.caption("Prompts folder: ./prompts/")

st.markdown('<p class="title-text">Phenomics Portal</p>', unsafe_allow_html=True)
st.markdown("##### Phenomics 期刊全渠道成果发布系统")

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown("#### 📄 论文输入")
    uploaded_file = st.file_uploader("上传 PDF 原文", type="pdf", label_visibility="collapsed")
    manual_input = st.text_area("或在此粘贴内容摘要:", height=200)

    # 动态读取 prompts 文件夹下的渠道文件
    prompts_dir = "./prompts"
    channel_files = []
    channel_names = []
    if os.path.exists(prompts_dir):
        for f in os.listdir(prompts_dir):
            if f.endswith(".txt"):
                channel_files.append(f)
                channel_names.append(os.path.splitext(f)[0])  # 去掉扩展名作为显示名称

    st.markdown("#### 🚀 生成选项")
    selected_channels = {}
    for name in channel_names:
        selected_channels[name] = st.checkbox(f"生成 {name} 内容", value=True)

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
                # 初始化结果存储
                if "results" not in st.session_state:
                    st.session_state.results = {}

                with st.status("正在进行多模态内容编排...", expanded=True) as status:
                    for name in channel_names:
                        if selected_channels.get(name, False):
                            st.write(f"正在生成 {name} 内容...")
                            # 读取对应提示词文件
                            file_path = os.path.join(prompts_dir, f"{name}.txt")
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    system_prompt = f.read()
                                result = generate_content(client, source_text, system_prompt)
                                st.session_state.results[name] = result
                            except Exception as e:
                                st.error(f"读取或生成 {name} 失败: {e}")
                                st.session_state.results[name] = f"错误: {e}"
                    status.update(label="✨ 内容全部生成完毕!", state="complete", expanded=False)

                # 动态创建标签页显示结果
                tabs = st.tabs([f"📄 {name}" for name in channel_names if selected_channels.get(name, False)])
                tab_index = 0
                for name in channel_names:
                    if selected_channels.get(name, False):
                        with tabs[tab_index]:
                            st.markdown(f"##### {name} 内容")
                            st.info(st.session_state.results.get(name, "生成失败"))
                            # 提供下载按钮
                            st.download_button(
                                label=f"下载 {name} 稿件",
                                data=st.session_state.results.get(name, ""),
                                file_name=f"{name}_release.txt"
                            )
                        tab_index += 1
    else:
        st.info("系统就绪。请上传 PDF 论文原文，系统将自动提取信息并完成全渠道排版。")

st.markdown("---")
st.markdown('<p style="text-align: center; color: #64748b; font-size: 0.8rem;">Phenomics Intelligence System v5.1 | Dynamic Prompts</p>', unsafe_allow_html=True)
