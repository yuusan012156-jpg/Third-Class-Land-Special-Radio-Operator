import streamlit as st
import pandas as pd
import random
import re

# アプリの基本設定
st.set_page_config(page_title="エックス線作業主任者 過去問演習", page_icon="☢️")

# --- データの読み込み ---
@st.cache_data
def load_data():
    try:
        # utf-8-sig で読み込み
        df = pd.read_csv("quiz_data.csv", encoding="utf-8-sig")
        # 前後の空白削除
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # 選択肢の分割ロジック
        def split_options(x):
            s = str(x)
            if '|' in s:
                return [i.strip() for i in s.split('|')]
            parts = re.split(r'(?=（[１２３４５12345]）)', s)
            return [p.strip() for p in parts if p.strip()]

        df['options'] = df['options'].apply(split_options)
        df['answer'] = df['answer'].astype(str)
        return df
    except Exception as e:
        st.error(f"エラー: quiz_data.csv の読み込みに失敗しました。{e}")
        st.stop()

df_all = load_data()

# --- セッション管理の初期化 ---
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

def start_quiz(selected_session, category_filter):
    filtered = df_all[df_all['session'] == selected_session]
    if category_filter != "全科目一括":
        filtered = filtered[filtered['category'] == category_filter]

    def get_id_num(id_str):
        try:
            return int(re.sub(r'\D', '', str(id_str)))
        except:
            return 0

    filtered = filtered.sort_values(by='id', key=lambda x: x.apply(get_id_num))
    
    st.session_state.selected_questions = filtered.to_dict('records')
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.show_answer = False
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    st.session_state.category_scores = {}
    st.session_state.category_totals = {}
    st.session_state.wrong_answers = []

# --- メイン画面 ---
st.title("☢️ エックス線作業主任者 過去問演習")

if not st.session_state.quiz_started:
    # 選択画面
    sessions = sorted(df_all['session'].unique().tolist(), reverse=True)
    categories = ["全科目一括", "エックス線の管理に関する知識", "関係法令", "エックス線の測定に関する知識", "エックス線の生体に与える影響に関する知識"]

    col1, col2 = st.columns(2)
    with col1:
        selected_session = st.selectbox("実施回を選択", sessions)
    with col2:
        category_choice = st.selectbox("科目を選択", categories)

    st.info(f"「{selected_session}」の【{category_choice}】を開始します。")
    if st.button("テストを開始する", use_container_width=True):
        start_quiz(selected_session, category_choice)
        st.rerun()

elif not st.session_state.quiz_finished:
    # 問題回答画面
    current_questions = st.session_state.selected_questions
    
    if not current_questions:
        st.warning("条件に一致する問題が見つかりませんでした。")
        if st.button("メニューに戻る"):
            st.session_state.quiz_started = False
            st.rerun()
    else:
        current_q = current_questions[st.session_state.idx]
        
        # 進行度表示とホームボタン
        col_id, col_home = st.columns([4, 1])
        with col_id:
            st.caption(f"{current_q['session']} ／ {current_q['category']}")
            st.subheader(f"{current_q['id']} （{st.session_state.idx + 1} / {len(current_questions)} 問目）")
        with col_home:
            if st.button("🏠 ホーム", help="メニューに戻ります"):
                st.session_state.quiz_started = False
                st.rerun()

        st.progress((st.session_state.idx) / len(current_questions))
        
        # --- 質問文の整形（ABCDの段落分けと太字化） ---
        q_text = str(current_q['question'])
        # A: B: などを検知して改行を入れる
        q_text = re.sub(r'\s*([A-E][:：])\s*', r'\n\n\1 ', q_text)
        # 全体を太字にする
        st.markdown(f"#### **{q_text}**")
        
        user_ans = st.radio("選択肢を選んでください:", current_q['options'], key=f"q_{st.session_state.idx}")
        
        if not st.session_state.show_answer:
            if st.button("回答を確定する", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        else:
            # 正解判定
            user_choice_num = re.search(r'１|２|３|４|５|1|2|3|4|5', user_ans).group()
            correct_num = re.search(r'１|２|３|４|５|1|2|3|4|5', current_q['answer']).group()
            
            cat = current_q['category']
            if cat not in st.session_state.category_totals:
                st.session_state.category_totals[cat] = 0
                st.session_state.category_scores[cat] = 0
            
            # スコアの二重加算防止
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
            
            if st.button("次の問題へ", use_container_width=True):
                if st.session_state.idx + 1 < len(current_questions):
                    st.session_state.idx += 1
                    st.session_state.show_answer = False
                    st.rerun()
                else:
                    st.session_state.quiz_finished = True
                    st.rerun()

else:
    # テスト結果画面
    total = len(st.session_state.selected_questions)
    percent = (st.session_state.score / total) * 100
    st.header("🏁 テスト終了")
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("総合正解率", f"{percent:.1f}%")
    col_res2.metric("正解数", f"{st.session_state.score} / {total}")
    
    st.subheader("📊 分野別分析（足切り確認）")
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
        st.success("🎉 合格基準達成です！")
    else:
        st.warning("📉 合格には「総合6割」かつ「各科目4割」が必要です。")

    if st.session_state.wrong_answers:
        with st.expander("❌ 間違えた問題の復習"):
            for w_q in st.session_state.wrong_answers:
                st.markdown(f"**[{w_q['session']}] {w_q['id']}**: **{w_q['question']}**")
                st.write(f"正解: {w_q['answer']}")
                st.info(f"解説: {w_q['explanation']}")
                st.divider()

    if st.button("メニュー（ホーム）に戻る", use_container_width=True):
        st.session_state.quiz_started = False
        st.rerun()
