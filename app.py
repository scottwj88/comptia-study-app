import streamlit as st
import json
import os

# --- 1. 配置页面 ---
st.set_page_config(page_title="CompTIA A+ 刷题神器", page_icon="🛡️", layout="centered")

# ================= 🔐 安全门卫代码 (保留) =================
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

def check_password():
    # 如果没有在 secrets 配置密码，直接放行 (方便本地测试)
    if "my_password" not in st.secrets:
        return True
        
    if st.session_state.password_correct:
        return True

    st.text_input("请输入访问密码:", type="password", key="password_input", on_change=password_entered)
    return False

def password_entered():
    if st.session_state["password_input"] == st.secrets["my_password"]:
        st.session_state.password_correct = True
        del st.session_state["password_input"]
    else:
        st.error("❌ 密码错误")

if not check_password():
    st.stop()
# ========================================================

# --- 2. 动态加载数据函数 ---
def load_questions(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

# --- 3. 初始化 Session State ---
if 'current_subject' not in st.session_state:
    # 默认选择第一个
    st.session_state.current_subject = "Core 1 (220-1201) - 基础" 
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = [] 
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {} 

# --- 4. 侧边栏布局 ---
with st.sidebar:
    st.header("⚙️ 学习控制台")
    
    # === 科目选择器 (新增了 Core 2 ET 选项) ===
    subject_selection = st.radio(
        "📚 选择考试科目:", 
        [
            "Core 1 (220-1201) - 基础", 
            "Core 1 (220-1201) - ET高难版", 
            "Core 2 (220-1202) - 基础",
            "Core 2 (220-1202) - ET高难版"  # <--- 新增这项
        ]
    )
    
    # === 检测科目切换并重置进度 ===
    if subject_selection != st.session_state.current_subject:
        st.session_state.current_subject = subject_selection
        st.session_state.current_q_index = 0
        st.session_state.user_answers = {}
        st.rerun()

    # === 根据选择确定文件名 (逻辑更新) ===
    if "Core 1" in subject_selection:
        if "ET" in subject_selection:
            current_file = "et_questions_core1.json"
        else:
            current_file = "questions_core1.json"
    else: # Core 2
        if "ET" in subject_selection:
            current_file = "et_questions_core2.json" # <--- 新增映射
        else:
            current_file = "questions_core2.json"

    # 加载对应题库
    questions = load_questions(current_file)
    st.write(f"当前题库数量: {len(questions)}")
    
    st.divider()

    # 模式切换
    mode = st.radio("选择模式:", ["📝 模拟考试 (Practice)", "📕 错题回顾 (Review)"])
    
    if mode == "📝 模拟考试 (Practice)":
        st.session_state.quiz_mode = 'practice'
        active_questions = questions
    else:
        st.session_state.quiz_mode = 'review'
        active_questions = [q for q in questions if q['id'] in st.session_state.mistakes]

    # 防崩盘逻辑
    if len(active_questions) > 0 and st.session_state.current_q_index >= len(active_questions):
        st.session_state.current_q_index = 0

    # 进度条
    if len(active_questions) > 0:
        progress = st.session_state.current_q_index / len(active_questions)
        st.progress(progress)
        st.write(f"进度: {st.session_state.current_q_index + 1} / {len(active_questions)}")
    else:
        if st.session_state.quiz_mode == 'review':
            st.info("👏 当前科目没有错题！")
    
    st.divider()
    
    # 重置按钮
    if st.button("🔄 重置当前进度"):
        st.session_state.current_q_index = 0
        st.session_state.user_answers = {}
        st.rerun()

# --- 5. 主界面逻辑 ---

st.title(f"🛡️ {subject_selection}")

if not active_questions:
    if st.session_state.quiz_mode == 'review':
        st.success("🎉 太棒了！本轮复习完毕。")
    else:
        # 如果文件不存在，给出更明确的提示
        st.error(f"⚠️ 未找到题库文件: `{current_file}`")
        st.info("请确认你是否已创建该文件并上传到 GitHub。")
else:
    # --- 1. 防止索引越界 ---
    if st.session_state.current_q_index >= len(active_questions):
        st.session_state.current_q_index = 0
        
    current_q = active_questions[st.session_state.current_q_index]
    q_id = current_q['id']

    # --- 2. 显示题目 ---
    st.markdown(f"### Q{st.session_state.current_q_index + 1}: {current_q['question']}")
    
    # 动态标签颜色
    if "Core 1" in current_q['category']:
        st.caption(f"🏷️ :blue[{current_q['category']}]")
    else:
        st.caption(f"🏷️ :red[{current_q['category']}]")

    # 检查是否已回答
    user_has_answered = q_id in st.session_state.user_answers

    # --- 3. 答题区域 ---
    if not user_has_answered:
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
        my_choice = st.session_state.user_answers[q_id]
        st.radio("请选择答案:", current_q['options'], index=current_q['options'].index(my_choice), disabled=True)

        if my_choice == current_q['answer']:
            st.success("✅ 回答正确！")
        else:
            st.error(f"❌ 回答错误。正确答案是: {current_q['answer']}")
            if q_id not in st.session_state.mistakes:
                st.session_state.mistakes.append(q_id)
        
        st.info(f"💡 **解析:** {current_q['explanation']}")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.session_state.current_q_index < len(active_questions) - 1:
                if st.button("下一题 ➡️"):
                    st.session_state.current_q_index += 1
                    st.rerun()
            else:
                st.success("🏁 本章题目已做完！")
                if st.button("🔄 重新开始"):
                    st.session_state.current_q_index = 0
                    st.rerun()

    # --- 4. 底部跳转栏 ---
    st.markdown("---")
    st.write("📍 **快速跳转**")
    col_jump1, col_jump2 = st.columns([4, 1])
    with col_jump1:
        target_q = st.number_input("输入题号", min_value=1, max_value=len(active_questions), value=st.session_state.current_q_index + 1)
    with col_jump2:
        st.write(""); st.write("")
        if st.button("Go 🚀"):
            st.session_state.current_q_index = target_q - 1
            st.rerun()
