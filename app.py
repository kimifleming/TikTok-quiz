import streamlit as st
import pandas as pd
import os
import random

# Configuration and File Paths
DATA_FILE = "submissions.csv"
SCORE_FILE = "scores.csv"

def save_submission(name, link):
    new_data = pd.DataFrame([[name, link]], columns=["Name", "Link"])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    df.to_csv(DATA_FILE, index=False)

def update_score(player_name):
    if os.path.exists(SCORE_FILE):
        scores = pd.read_csv(SCORE_FILE)
    else:
        scores = pd.DataFrame(columns=["Player", "Points"])
    if player_name in scores["Player"].values:
        scores.loc[scores["Player"] == player_name, "Points"] += 1
    else:
        new_score = pd.DataFrame([[player_name, 1]], columns=["Player", "Points"])
        scores = pd.concat([scores, new_score], ignore_index=True)
    scores.to_csv(SCORE_FILE, index=False)

# UI Setup
st.set_page_config(page_title="TikTok Mystery Quiz", layout="wide")
st.title("🎬 TikTok Mystery Quiz")

# Sidebar for Setup & Game State
st.sidebar.header("⚙️ Game Control")
game_mode = st.sidebar.toggle("Activate Quiz Mode", value=False)

if not game_mode:
    st.header("Step 1: Submit your TikTok")
    with st.form("submission_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        tiktok_url = st.text_input("Paste TikTok Link here")
        submit = st.form_submit_button("Submit Privately")
        if submit and name and tiktok_url:
            save_submission(name, tiktok_url)
            st.success(f"Nice one, {name}! Your submission is hidden.")

else:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'current_idx' not in st.session_state:
            st.session_state.current_idx = 0
            st.session_state.order = random.sample(range(len(df)), len(df))
            st.session_state.answered = False

        col_main, col_side = st.columns([3, 1])
        with col_main:
            if st.session_state.current_idx < len(df):
                current_row = df.iloc[st.session_state.order[st.session_state.current_idx]]
                st.subheader(f"Video {st.session_state.current_idx + 1} of {len(df)}")
                st.video(current_row['Link'])
                st.write("### ❓ Who submitted this?")
                all_names = sorted(df['Name'].unique().tolist())
                btn_cols = st.columns(2)
                for i, participant in enumerate(all_names):
                    if btn_cols[i % 2].button(participant, key=f"p_{participant}_{st.session_state.current_idx}"):
                        if participant == current_row['Name']:
                            st.balloons()
                            st.success(f"CORRECT! It was {participant}!")
                            if not st.session_state.answered:
                                update_score(participant)
                                st.session_state.answered = True
                if st.session_state.answered:
                    if st.button("Next Video ➡️"):
                        st.session_state.current_idx += 1
                        st.session_state.answered = False
                        st.rerun()
            else:
                st.header("🏆 Quiz Finished!")
        with col_side:
            st.write("### 🥇 Leaderboard")
            if os.path.exists(SCORE_FILE):
                st.table(pd.read_csv(SCORE_FILE).sort_values(by="Points", ascending=False))
    else:
        st.warning("No submissions yet!")
