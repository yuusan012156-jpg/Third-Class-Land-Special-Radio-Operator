import streamlit as st
import pandas as pd
import random

# アプリの基本設定
st.set_page_config(page_title="エックス線作業主任者 模擬テスト", page_icon="☢️")

# --- データの読み込み ---
@st.cache_data
def load_data():
    try:
        # utf-8-sig で読み込み
        df = pd.read_csv("quiz_data.csv", encoding="utf-8-sig")
        # 前後の空白削除と型変換
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # 選択肢をリストに変換
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

def start_quiz(selected_session, category_filter):
    # 1. 実施回でフィルタリング
    filtered_pool = [q for q in quiz_pool if q['session'] == selected_session]
    
    # 2. カテゴリでフィルタリング
    if category_filter != "全科目一括":
        filtered_pool = [q for q in filtered_pool if q['category'] == category_filter]

    # 実施回別なので、問題番号順にソート（ランダムにしない）
    st.session_state.selected_questions = sorted(filtered_pool, key=lambda x: x['id'])
    
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.show_answer = False
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    st.session_state.category_scores = {}
    st.session_state.category_totals = {}
    st.session_state.wrong_answers = []

st.title("☢️ エックス線作業主任者 模擬テスト")
st.caption("過去問をマスターして、足切りラインを確実に突破しましょう")

if not st.session_state.quiz_started:
    # 実施回のリスト定義
    sessions = [
        "2025年（令和7年）10月公表分", "2025年（令和7年）4月公表分", "2024年（令和6年）10月公表分",
        "2024年（令和6年）4月公表分", "2023年（令和5年）10月公表分", "2023年（令和5年）4月公表分",
        "2022年（令和4年）10月公表分", "2022年（令和4年）4月公表分", "2021年（令和3年）10月公表分",
        "2021年（令和3年）4月公表分", "2020年（令和2年）10月公元分"
    ]
    
    categories = ["全科目一括", "エックス線の管理に関する知識", "関係法令", "エックス線の測定に関する知識", "エックス線の生体に与える影響に関する知識"]

    col1, col2 = st.columns(2)
    with col1:
        selected_session = st.selectbox("実施回を選択", sessions)
    with col2:
        category_choice = st.selectbox("科目を選択", categories)

    st.info(f"【{selected_session}】の【{category_choice}】を開始します。")
    if st.button("模擬テストを開始する"):
        start_quiz(selected_session, category_choice)
        st.rerun()

elif not st.session_state.quiz_finished:
    current_questions = st.session_state.selected_questions
    
    if not current_questions:
        st.warning("選択された条件に該当する問題が見つかりませんでした。")
        if st.button("メニューに戻る"):
            st.session_state.quiz_started = False
            st.rerun()
    else:
        current_q = current_questions[st.session_state.idx]
        
        st.progress((st.session_state.idx) / len(current_questions))
        st.subheader(f"{current_q['id']} / {len(current_questions)}")
        st.markdown(f"**分野: {current_q['category']}**")
        st.markdown(f"#### {current_q['question']}")
        
        user_ans = st.radio("選択肢を選んでください:", current_q['options'], key=f"q_{st.session_state.idx}")
        
        if not st.session_state.show_answer:
            if st.button("回答を確定する"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            # 正解判定（カッコの全角半角やインデックスに対応できるよう先頭文字で比較）
            user_choice_num = user_ans[1:2] # （１）の1の部分
            correct_num = current_q['answer'][1:2]
            cat = current_q['category']
            
            if cat not in st.session_state.category_totals:
                st.session_state.category_totals[cat] = 0
                st.session_state.category_scores[cat] = 0
            
            if 'last_idx' not in st.session_state or st.session_state.last_idx != st.session_state.idx:
                st.session_state.category_totals[cat] += 1
                if user_choice_num == correct_num:
                    st.session_state.score += 1
                    st.session_state.category_scores[cat] += 1
                else:
                    st.session_state.wrong_answers.append(current_q)
                st.session_state.last_idx = st.session_state.idx

            if user_choice_num == correct_num:
                st.success("✨ 正解！")
            else:
                st.error(f"❌ 不正解... 正解は 「{current_q['answer']}」")
            
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
    
    st.subheader("📊 分野別分析（足切り確認用）")
    for cat in st.session_state.category_totals:
        cat_score = st.session_state.category_scores[cat]
        cat_total = st.session_state.category_totals[cat]
        cat_percent = (cat_score / cat_total) * 100
        
        if cat_percent < 40:
            st.error(f"**{cat}**: {cat_percent:.1f}% ({cat_score}/{cat_total}) ⚠️ 足切りライン未満")
        else:
            st.success(f"**{cat}**: {cat_percent:.1f}% ({cat_score}/{cat_total}) ✅ クリア")

    if percent >= 60 and all((s/t)*100 >= 40 for s, t in zip(st.session_state.category_scores.values(), st.session_state.category_totals.values())):
        st.balloons()
        st.success("🎉 合格基準達成！おめでとうございます！")
    else:
        st.warning("📉 合格基準に達していません。復習を続けましょう。")

    if st.session_state.wrong_answers:
        with st.expander("❌ 間違えた問題の復習"):
            for i, w_q in enumerate(st.session_state.wrong_answers):
                st.markdown(f"**{w_q['id']}: {w_q['question']}**")
                st.write(f"・正解: {w_q['answer']}")
                st.info(f"解説: {w_q['explanation']}")
                st.divider()

    if st.button("もう一度挑戦"):
        st.session_state.quiz_started = False
        st.rerun()
