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

# --- 4. 侧边栏布局 ---
with st.sidebar:
    st.header("⚙️ 学习控制台")
    st.write(f"当前题库数量: {len(questions)}")
    
    # 模式切换
    mode = st.radio("选择模式:", ["📝 模拟考试 (Practice)", "📕 错题回顾 (Review)"])
    
    if mode == "📝 模拟考试 (Practice)":
        st.session_state.quiz_mode = 'practice'
        active_questions = questions
    else:
        st.session_state.quiz_mode = 'review'
        # 筛选出出错的题目
        active_questions = [q for q in questions if q['id'] in st.session_state.mistakes]

    # 进度条
    if len(active_questions) > 0:
        progress = (st.session_state.current_q_index / len(active_questions))
        st.progress(progress)
        st.write(f"进度: {st.session_state.current_q_index + 1} / {len(active_questions)}")
    
    # 重置按钮
    if st.button("🔄 重置进度"):
        st.session_state.current_q_index = 0
        st.session_state.score = 0
        st.session_state.user_answers = {}
        st.rerun()

# --- 5. 主界面逻辑 (修复版) ---

st.title("🛡️ CompTIA A+ (Series 1200)")

if not active_questions:
    if st.session_state.quiz_mode == 'review':
        st.success("🎉 太棒了！你目前没有错题记录，或者已经全部复习完毕。")
        st.info("请切换回“模拟考试”模式继续刷题。")
    else:
        st.error("未找到题目数据，请检查 questions.json 文件。")
else:
    # 获取当前题目
    if st.session_state.current_q_index >= len(active_questions):
        st.session_state.current_q_index = 0
        
    current_q = active_questions[st.session_state.current_q_index]
    q_id = current_q['id']

    # 显示题目
    st.markdown(f"### Q{st.session_state.current_q_index + 1}: {current_q['question']}")
    st.caption(f"Category: {current_q['category']}")

    # --- 核心修改点：先判断这道题是否做过 ---
    # 检查 session_state 中是否已经有这道题的答案记录
    user_has_answered = q_id in st.session_state.user_answers

    # 选项表单
    with st.form(key=f"form_{q_id}"):
        # 获取之前的选择（如果有）
        pre_selection = st.session_state.user_answers.get(q_id, None)
        
        user_choice = st.radio(
            "请选择答案:", 
            current_q['options'], 
            index=None if pre_selection is None else current_q['options'].index(pre_selection),
            # 这是一个优化：如果已经回答过，就禁用选项，防止重复提交
            disabled=user_has_answered 
        )
        
        # 只有没做过的时候，才显示提交按钮
        if not user_has_answered:
            submit_btn = st.form_submit_button("提交答案")
        else:
            submit_btn = False

    # --- 6. 逻辑处理 ---
    
    # 情况A：用户刚刚点击了提交
    if submit_btn and user_choice:
        # 记录答案
        st.session_state.user_answers[q_id] = user_choice
        # 关键！立即刷新页面，让页面进入“已回答状态”
        st.rerun()
    
    # 情况B：用户已经回答过这道题（无论是刚刚提交的，还是之前提交的）
    if user_has_answered:
        my_choice = st.session_state.user_answers[q_id]
        
        # 显示判定结果
        if my_choice == current_q['answer']:
            st.success("✅ 回答正确！")
            if st.session_state.quiz_mode == 'review' and submit_btn:
                st.balloons()
        else:
            st.error(f"❌ 回答错误。正确答案是: {current_q['answer']}")
            # 加入错题本
            if q_id not in st.session_state.mistakes:
                st.session_state.mistakes.append(q_id)
            
        # 显示解析
        st.info(f"💡 **解析:** {current_q['explanation']}")
        
        # --- 下一题按钮 (现在放在了表单外面，且只要回答过就会显示) ---
        if st.session_state.current_q_index < len(active_questions) - 1:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("下一题 ➡️"):
                    st.session_state.current_q_index += 1
                    st.rerun()
        else:
            st.success("🏁 本轮题目已做完！")
            if st.button("🔄 重新开始"):
                st.session_state.current_q_index = 0
                # st.session_state.user_answers = {} # 如果想保留答案记录，这行可以注释掉
                st.rerun()

    elif submit_btn and not user_choice:
        st.warning("⚠️ 请先选择一个选项。")
