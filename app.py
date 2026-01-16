import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px

# Files
DATA_FILE = "submissions.csv"
GUESS_FILE = "guesses.csv"
STATE_FILE = "game_state.txt"

# Ensure video directory exists
if not os.path.exists("videos"):
    os.makedirs("videos")

# --- Helper Functions ---
def get_state():
    if not os.path.exists(STATE_FILE): return "submitting"
    try:
        with open(STATE_FILE, "r") as f: return f.read().strip()
    except:
        return "submitting"

def set_state(state):
    with open(STATE_FILE, "w") as f: f.write(state)

def save_submission(name, video_file):
    file_path = os.path.join("videos", f"{int(time.time())}_{name}.mp4")
    with open(file_path, "wb") as f:
        f.write(video_file.getbuffer())
    
    new_data = pd.DataFrame([[name, file_path]], columns=["Name", "VideoPath"])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    df.to_csv(DATA_FILE, index=False)

def save_guess(video_owner, guessed_name, comment, guesser_name):
    new_guess = pd.DataFrame([[video_owner, guessed_name, comment, guesser_name]], 
                             columns=["Owner", "Guess", "Comment", "Guesser"])
    if os.path.exists(GUESS_FILE):
        df = pd.read_csv(GUESS_FILE)
        df = pd.concat([df, new_guess], ignore_index=True)
    else:
        df = new_guess
    df.to_csv(GUESS_FILE, index=False)

def full_reset():
    for f in [DATA_FILE, GUESS_FILE, STATE_FILE]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists("videos"):
        for f in os.listdir("videos"):
            try: os.remove(os.path.join("videos", f))
            except: pass
    st.session_state.clear()
    st.rerun()

# --- UI Setup ---
st.set_page_config(page_title="The Glizzy Quiz", page_icon="🌭")

# Global Reset Logic
def global_footer():
    st.write("")
    st.divider()
    with st.expander("🏠 Return to Home / Reset"):
        st.write("Wipes all data and returns to start.")
        if st.button("Reset & Return to Home", type="secondary", use_container_width=True):
            st.session_state.wants_reset = True
    
    if st.session_state.get("wants_reset", False):
        st.error("‼️ Delete everything?")
        rc1, rc2 = st.columns(2)
        if rc1.button("🔥 YES", key="g_reset_yes"): full_reset()
        if rc2.button("🚫 NO", key="g_reset_no"): 
            st.session_state.wants_reset = False
            st.rerun()

# --- MAIN APP LOGIC ---
current_state = get_state()

try:
    if current_state == "submitting":
        st.title("🌭 Step 1: Submissions")
        if st.session_state.get('submitted', False):
            st.success("✅ Thanks for submitting! If all other Glizzys have submitted, create the quiz below.")
        
        if os.path.exists(DATA_FILE):
            st.metric("Glizzys Collected", len(pd.read_csv(DATA_FILE)))

        with st.form("sub_form", clear_on_submit=True):
            name = st.text_input("Your Name")
            video = st.file_uploader("Upload video", type=["mp4", "mov", "avi"])
            if st.form_submit_button("Submit"):
                if name and video:
                    save_submission(name, video)
                    st.session_state.submitted = True
                    st.rerun()
        
        st.divider()
        if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
            st.session_state.confirm_quiz = True
        
        # Updated Confirmation Message
        if st.session_state.get("confirm_quiz", False):
            st.warning("⚠️ **Please make sure all entrance have submitted before continuing.**")
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, everyone is in", key="q_yes"):
                set_state("quiz"); st.session_state.confirm_quiz = False; st.rerun()
            if c2.button("❌ No, still waiting", key="q_no"):
                st.session_state.confirm_quiz = False; st.rerun()

    elif current_state == "quiz":
        st.title("🎬 Who Posted This?")
        df = pd.read_csv(DATA_FILE)
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        
        if st.session_state.q_idx < len(df):
            row = df.iloc[st.session_state.q_idx]
            st.write(f"**Video {st.session_state.q_idx + 1} of {len(df)}**")
            st.video(row['VideoPath'])
            
            guesser = st.text_input("Your Name", key="guesser_name")
            comment = st.text_area("Why them?")
            names = sorted(df['Name'].unique().tolist())
            cols = st.columns(2)
            for i, n in enumerate(names):
                if cols[i%2].button(n, key=f"g_{i}", use_container_width=True):
                    if not guesser: st.error("Name required!")
                    else:
                        save_guess(row['Name'], n, comment, guesser)
                        st.session_state.q_idx += 1; st.rerun()
        else:
            if st.button("📊 SHOW RESULTS", type="primary", use_container_width=True):
                set_state("results"); st.rerun()

    elif current_state == "results":
        st.title("📊 Final Results")
        df = pd.read_csv(DATA_FILE)
        guesses_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()

        for i, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"Video #{i+1}")
                st.video(row['VideoPath'])
                
                v_guesses = guesses_df[guesses_df['Owner'] == row['Name']] if not guesses_df.empty else pd.DataFrame()
                if not v_guesses.empty:
                    fig = px.pie(v_guesses['Guess'].value_counts().reset_index(), values='count', names='Guess', title="Votes")
                    st.plotly_chart(fig, use_container_width=True)
                
                if st.button(f"✨ REVEAL OWNER ✨", key=f"rev_{i}", use_container_width=True):
                    st.balloons(); st.warning(f"THE OWNER: {row['Name']}")

        if not guesses_df.empty:
            st.divider()
            st.header("🏆 Leaderboard")
            # Calculate correct guesses, excluding people guessing their own video
            guesses_df['correct'] = (guesses_df['Owner'] == guesses_df['Guess']) & (guesses_df['Guesser'] != guesses_df['Owner'])
            leaderboard = guesses_df.groupby('Guesser')['correct'].sum().reset_index()
            leaderboard = leaderboard.sort_values(by='correct', ascending=False)
            st.table(leaderboard.rename(columns={'correct': 'Points'}))

except Exception as e:
    st.error(f"App Error: {e}")

global_footer()
