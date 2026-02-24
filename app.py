import streamlit as st
import pandas as pd
import random

# アプリの基本設定
st.set_page_config(page_title="第3級陸上特殊無線技士 模擬テスト", page_icon="🏥")

# --- データの読み込み ---
@st.cache_data
def load_data():
    try:
        # utf-8-sig で読み込み、前後の空白を自動削除
        df = pd.read_csv("quiz_data.csv", encoding="utf-8-sig")
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        df['options'] = df['options'].apply(lambda x: [i.strip() for i in str(x).split('|')])
        df['answer'] = df['answer'].astype(str)
        return df.to_dict('records')
    except Exception as e:
        st.error(f"エラー: quiz_data.csv の読み込みに失敗しました。{e}")
        st.stop()

quiz_pool = load_data()

# --- セッション管理の初期化 ---
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

def start_quiz(mode, category_filter):
    # カテゴリフィルタリング
    if category_filter == "すべて":
        filtered_pool = quiz_pool
    else:
        filtered_pool = [q for q in quiz_pool if q['category'] == category_filter]

    # 出題数の決定
    if mode == "本番モード (27問)":
        sample_size = min(27, len(filtered_pool))
    else:
        sample_size = min(50, len(filtered_pool))

    st.session_state.selected_questions = random.sample(filtered_pool, sample_size)
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.show_answer = False
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    # 分野別集計と間違えた問題の記録用
    st.session_state.category_scores = {}
    st.session_state.category_totals = {}
    st.session_state.wrong_answers = []

st.title("🏥 第3級陸上特殊無線技士 模擬テスト")
st.caption("制限時間なし：じっくり解説を読んで学習しましょう")

if not st.session_state.quiz_started:
    # 登録問題数の表示を修正
    st.write(f"現在の登録問題数: {len(quiz_pool)}問")
    
    # 改良ポイント：分野選択とモード選択
    col1, col2 = st.columns(2)
    with col1:
        category_choice = st.selectbox("出題分野を選択", ["すべて", "工学", "法規"])
    with col2:
        mode_choice = st.selectbox("テストモードを選択", ["練習モード (50問)", "本番モード (27問)"])

    st.info(f"「開始」を押すと、{category_choice}から問題をシャッフル出題します。")
    if st.button("模擬テストを開始する"):
        start_quiz(mode_choice, category_choice)
        st.rerun()

elif not st.session_state.quiz_finished:
    current_questions = st.session_state.selected_questions
    current_q = current_questions[st.session_state.idx]
    
    st.progress((st.session_state.idx) / len(current_questions))
    st.subheader(f"問題 {st.session_state.idx + 1} / {len(current_questions)}")
    st.markdown(f"**分野: {current_q['category']}**")
    st.markdown(f"#### {current_q['question']}")
    
    user_ans = st.radio("選択肢を選んでください:", current_q['options'], key=f"q_{st.session_state.idx}")
    
    if not st.session_state.show_answer:
        if st.button("回答を確定する"):
            st.session_state.show_answer = True
            st.rerun()
    else:
        user_choice_num = user_ans[0] 
        correct_num = current_q['answer']
        cat = current_q['category']
        
        # 初めての分野なら初期化
        if cat not in st.session_state.category_totals:
            st.session_state.category_totals[cat] = 0
            st.session_state.category_scores[cat] = 0
        
        if 'last_idx' not in st.session_state or st.session_state.last_idx != st.session_state.idx:
            st.session_state.category_totals[cat] += 1
            if user_choice_num == correct_num:
                st.session_state.score += 1
                st.session_state.category_scores[cat] += 1
            else:
                # 間違えた問題を記録
                st.session_state.wrong_answers.append(current_q)
            st.session_state.last_idx = st.session_state.idx

        if user_choice_num == correct_num:
            st.success("✨ 正解！")
        else:
            full_correct_text = next((opt for opt in current_q['options'] if opt.startswith(correct_num)), correct_num)
            st.error(f"❌ 不正解... 正解は 「{full_correct_text}」")
        
        st.info(f"💡 **解説:**\n\n{current_q['explanation']}")
        
        if st.button("次の問題へ"):
            if st.session_state.idx + 1 < len(current_questions):
                st.session_state.idx += 1
                st.session_state.show_answer = False
                st.rerun()
            else:
                st.session_state.quiz_finished = True
                st.rerun()
else:
    # 結果表示
    total = len(st.session_state.selected_questions)
    percent = (st.session_state.score / total) * 100
    st.header("🏁 テスト終了")
    
    col1, col2 = st.columns(2)
    col1.metric("総合正解率", f"{percent:.1f}%")
    col2.metric("正解数", f"{st.session_state.score} / {total}")
    
    # 改良ポイント：分野別の得点率表示
    st.subheader("📊 分野別分析")
    for cat in st.session_state.category_totals:
        cat_score = st.session_state.category_scores[cat]
        cat_total = st.session_state.category_totals[cat]
        cat_percent = (cat_score / cat_total) * 100
        st.write(f"**{cat}**: {cat_percent:.1f}% ({cat_score}/{cat_total})")

    if percent >= 80:
        st.balloons()
        st.success("🎉 合格ラインクリア！")
    else:
        st.warning("📉 不合格判定です。復習しましょう。")

    # 改良ポイント：間違えた問題の一覧表示
    if st.session_state.wrong_answers:
        with st.expander("❌ 間違えた問題の復習"):
            for i, w_q in enumerate(st.session_state.wrong_answers):
                st.markdown(f"**問 {i+1}: {w_q['question']}**")
                st.write(f"・選択肢: {', '.join(w_q['options'])}")
                # 番号から正解の文章を復元
                c_num = w_q['answer']
                c_text = next((opt for opt in w_q['options'] if opt.startswith(c_num)), c_num)
                st.write(f"・正解: {c_text}")
                st.info(f"解説: {w_q['explanation']}")
                st.divider()

    if st.button("もう一度挑戦"):
        st.session_state.quiz_started = False
        st.rerun()