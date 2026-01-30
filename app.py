import streamlit as st
import json
import os

# --- 1. 配置页面 ---
st.set_page_config(page_title="CompTIA A+ 2026 刷题神器", page_icon="🛡️", layout="centered")

# --- 2. 加载数据函数 ---
@st.cache_data
def load_questions():
    # 尝试加载本地 json 文件
    if os.path.exists('questions.json'):
        with open('questions.json', 'r') as f:
            return json.load(f)
    return []

# --- 3. 初始化 Session State (关键：用于记录状态) ---
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = [] # 存储错题 ID
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = 'practice' # practice 或 review
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {} # 记录用户选了什么

# 加载题目
questions = load_questions()

# --- 4. 侧边栏布局 (防崩盘修复版) ---
with st.sidebar:
    st.header("⚙️ 学习控制台")
    st.write(f"总题库数量: {len(questions)}")
    
    # 模式切换
    mode = st.radio("选择模式:", ["📝 模拟考试 (Practice)", "📕 错题回顾 (Review)"])
    
    if mode == "📝 模拟考试 (Practice)":
        st.session_state.quiz_mode = 'practice'
        active_questions = questions
    else:
        st.session_state.quiz_mode = 'review'
        # 筛选出出错的题目
        active_questions = [q for q in questions if q['id'] in st.session_state.mistakes]

    # --- 关键修复点：先纠正索引，再画进度条 ---
    # 如果当前页码超过了题目总数（比如从100题的模式切到只有1题的错题本），强制归零
    if len(active_questions) > 0 and st.session_state.current_q_index >= len(active_questions):
        st.session_state.current_q_index = 0

    # 进度条
    if len(active_questions) > 0:
        # 现在的 index 肯定是安全的
        progress = st.session_state.current_q_index / len(active_questions)
        st.progress(progress)
        st.write(f"进度: {st.session_state.current_q_index + 1} / {len(active_questions)}")
    else:
        if st.session_state.quiz_mode == 'review':
            st.info("👏 目前没有错题！")
            st.caption("去练习模式多刷几道吧~")
    
    st.divider()
    
    # 重置按钮
    if st.button("🔄 重置所有进度"):
        st.session_state.current_q_index = 0
        st.session_state.score = 0
        st.session_state.user_answers = {}
        st.session_state.mistakes = [] # 可选：是否连错题本也清空
        st.rerun()

# --- 5. 主界面逻辑 (含跳转功能版) ---

st.title("🛡️ CompTIA A+ (Series 1200)")

if not active_questions:
    if st.session_state.quiz_mode == 'review':
        st.success("🎉 太棒了！你目前没有错题记录，或者已经全部复习完毕。")
        st.info("请切换回“模拟考试”模式继续刷题。")
    else:
        st.error("未找到题目数据，请检查 questions.json 文件。")
else:
    # --- 1. 防止索引越界 (安全检查) ---
    if st.session_state.current_q_index >= len(active_questions):
        st.session_state.current_q_index = 0
        
    current_q = active_questions[st.session_state.current_q_index]
    q_id = current_q['id']

    # --- 2. 显示题目 ---
    st.markdown(f"### Q{st.session_state.current_q_index + 1}: {current_q['question']}")
    st.caption(f"Category: {current_q['category']}")

    # 检查是否已回答
    user_has_answered = q_id in st.session_state.user_answers

    # --- 3. 答题区域 (Scenario A: 未答 | Scenario B: 已答) ---
    if not user_has_answered:
        # [未回答] 显示表单和提交按钮
        with st.form(key=f"form_{q_id}"):
            user_choice = st.radio("请选择答案:", current_q['options'], index=None)
            submit_btn = st.form_submit_button("提交答案")
        
        if submit_btn:
            if user_choice:
                st.session_state.user_answers[q_id] = user_choice
                st.rerun()
            else:
                st.warning("⚠️ 请先选择一个选项。")

    else:
        # [已回答] 显示结果和解析（只读模式）
        my_choice = st.session_state.user_answers[q_id]
        
        st.radio(
            "请选择答案:", 
            current_q['options'], 
            index=current_q['options'].index(my_choice), 
            disabled=True 
        )

        if my_choice == current_q['answer']:
            st.success("✅ 回答正确！")
        else:
            st.error(f"❌ 回答错误。正确答案是: {current_q['answer']}")
            if q_id not in st.session_state.mistakes:
                st.session_state.mistakes.append(q_id)
        
        st.info(f"💡 **解析:** {current_q['explanation']}")
        
        # 下一题按钮
        if st.session_state.current_q_index < len(active_questions) - 1:
            if st.button("下一题 ➡️"):
                st.session_state.current_q_index += 1
                st.rerun()
        else:
            st.success("🏁 本轮题目已做完！")
            if st.button("🔄 重新开始"):
                st.session_state.current_q_index = 0
                st.rerun()

    # --- 4. 底部跳转栏 (新增功能) ---
    st.markdown("---") # 分割线
    st.write("📍 **快速跳转**")
    
    col_jump1, col_jump2 = st.columns([4, 1])
    
    with col_jump1:
        # 输入框：默认显示当前题号，最大值限制为题目总数
        target_q = st.number_input(
            "输入题号 (1 - {})".format(len(active_questions)),
            min_value=1, 
            max_value=len(active_questions), 
            value=st.session_state.current_q_index + 1
        )
        
    with col_jump2:
        st.write("") # 占位符，为了对齐
        st.write("") 
        if st.button("Go 🚀"):
            # 注意：用户输入的是 1 开始的，我们要转成 0 开始的索引
            st.session_state.current_q_index = target_q - 1
            st.rerun()
