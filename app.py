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
        # utf-8-sig で読み込み（Excel等で作ったCSVの文字化け対策）
        df = pd.read_csv("quiz_data.csv", encoding="utf-8-sig")
        
        # 前後の空白削除
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # 選択肢の分割ロジック
        def split_options(x):
            s = str(x)
            if '|' in s:
                return [i.strip() for i in s.split('|')]
            # | がない場合は （１）〜 で分割を試みる
            parts = re.split(r'(?=（[１２３４５１２３４５]）)', s)
            return [p.strip() for p in parts if p.strip()]

        df['options'] = df['options'].apply(split_options)
        df['answer'] = df['answer'].astype(str)
        return df
    except Exception as e:
        st.error(f"エラー: quiz_data.csv の読み込みに失敗しました。{e}")
        st.stop()

df_all = load_data()
quiz_pool = df_all.to_dict('records')

# --- セッション管理の初期化 ---
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

def start_quiz(selected_session, category_filter):
    # CSVから選択された回と科目に絞り込み
    filtered = df_all[df_all['session'] == selected_session]
    
    if category_filter != "全科目一括":
        filtered = filtered[filtered['category'] == category_filter]

    # ID（問1, 問2...）でソート
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

st.title("☢️ エックス線作業主任者 過去問演習")
st.caption("最新の公表問題に対応。科目ごとの足切り突破を目指しましょう。")

if not st.session_state.quiz_started:
    # CSVファイル内に存在する「実施回」を自動的に取得してリスト化
    sessions = sorted(df_all['session'].unique().tolist(), reverse=True)
    
    categories = ["全科目一括", "エックス線の管理に関する知識", "関係法令", "エックス線の測定に関する知識", "エックス線の生体に与える影響に関する知識"]

    col1, col2 = st.columns(2)
    with col1:
        selected_session = st.selectbox("実施回を選択", sessions)
    with col2:
        category_choice = st.selectbox("科目を選択", categories)

    st.info(f"「{selected_session}」の演習を開始します。")
    if st.button("テストを開始する"):
        start_quiz(selected_session, category_choice)
        st.rerun()

elif not st.session_state.quiz_finished:
    current_questions = st.session_state.selected_questions
    
    if not current_questions:
        st.warning("条件に一致する問題が見つかりませんでした。")
        if st.button("メニューに戻る"):
            st.session_state.quiz_started = False
            st.rerun()
    else:
        current_q = current_questions[st.session_state.idx]
        
        st.progress((st.session_state.idx) / len(current_questions))
        st.subheader(f"{current_q['id']} （{st.session_state.idx + 1} / {len(current_questions)} 問目）")
        st.markdown(f"**分野: {current_q['category']}**")
        
        # 質問文の整形（A: B: などを太字にして改行）
        q_text = str(current_q['question']).replace(" A ", "\n\n**A** ").replace(" B ", "\n\n**B** ").replace(" C ", "\n\n**C** ").replace(" D ", "\n\n**D** ")
        st.markdown(f"#### {q_text}")
        
        user_ans = st.radio("選択肢を選んでください:", current_q['options'], key=f"q_{st.session_state.idx}")
        
        if not st.session_state.show_answer:
            if st.button("回答を確定する"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            # 正解判定（全角・半角の差を吸収）
            user_choice_num = re.search(r'１|２|３|４|５|1|2|3|4|5', user_ans).group()
            correct_num = re.search(r'１|２|３|４|５|1|2|3|4|5', current_q['answer']).group()
            
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
    
    st.subheader("📊 分野別得点（足切り40%の確認）")
    for cat in st.session_state.category_totals:
        cat_score = st.session_state.category_scores[cat]
        cat_total = st.session_state.category_totals[cat]
        cat_percent = (cat_score / cat_total) * 100
        
        if cat_percent < 40:
            st.error(f"**{cat}**: {cat_percent:.1f}% ({cat_score}/{cat_total}) ⚠️ 足切り")
        else:
            st.success(f"**{cat}**: {cat_percent:.1f}% ({cat_score}/{cat_total}) ✅ クリア")

    if percent >= 60 and all((s/t)*100 >= 40 for s, t in zip(st.session_state.category_scores.values(), st.session_state.category_totals.values())):
        st.balloons()
        st.success("🎉 合格ライン達成です！この調子で頑張りましょう！")
    else:
        st.warning("📉 総合6割以上、かつ全科目4割以上が必要です。")

    if st.session_state.wrong_answers:
        with st.expander("❌ 間違えた問題を確認する"):
            for i, w_q in enumerate(st.session_state.wrong_answers):
                st.markdown(f"**{w_q['id']}: {w_q['question']}**")
                st.write(f"・正解: {w_q['answer']}")
                st.info(f"解説: {w_q['explanation']}")
                st.divider()

    if st.button("もう一度挑戦（メニューに戻る）"):
        st.session_state.quiz_started = False
        st.rerun()
