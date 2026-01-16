import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px

# Files
DATA_FILE = "submissions.csv"
GUESS_FILE = "guesses.csv"
STATE_FILE = "game_state.txt"

# Ensure a directory exists for the uploaded videos
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
current_state = get_state()

# --- MODE 1: SUBMITTING ---
if current_state == "submitting":
    st.title("🌭 Step 1: Submissions")
    
    if st.session_state.get('submitted', False):
        st.success("✅ Thanks for submitting! If all other Glizzy’s have submitted, create the quiz below.")
    
    if os.path.exists(DATA_FILE):
        st.metric("Glizzys Collected", len(pd.read_csv(DATA_FILE)))

    with st.form("sub_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        video = st.file_uploader("Upload your video", type=["mp4", "mov", "avi"])
        if st.form_submit_button("Submit Video"):
            if name and video:
                with st.spinner("Uploading Glizzy..."):
                    save_submission(name, video)
                st.session_state.submitted = True
                st.rerun()
            else:
                st.error("Missing name or video file!")
    
    st.divider()
    
    if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
        st.session_state.confirm_quiz = True

    if st.session_state.get("confirm_quiz", False):
        st.warning("⚠️ Has everyone submitted?")
        c1, c2 = st.columns(2)
        if c1.button("✅ YES", use_container_width=True):
            set_state("quiz")
            st.session_state.confirm_quiz = False
            st.rerun()
        if c2.button("❌ NO", use_container_width=True):
            st.session_state.confirm_quiz = False
            st.rerun()

# --- MODE 2: THE QUIZ ---
elif current_state == "quiz":
    st.title("🎬 Who Posted This?")
    if not os.path.exists(DATA_FILE):
        st.error("Data missing! Please reset.")
    else:
        df = pd.read_csv(DATA_FILE)
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        
        if st.session_state.q_idx < len(df):
            row = df.iloc[st.session_state.q_idx]
            st.write(f"**Video {st.session_state.q_idx + 1} of {len(df)}**")
            st.video(row['VideoPath'])
            
            st.divider()
            guesser = st.text_input("Your Name", key="guesser_name")
            comment = st.text_area("Your Comment")
            
            names = sorted(df['Name'].unique().tolist())
            cols = st.columns(2)
            for i, n in enumerate(names):
                if cols[i%2].button(n, key=f"guess_{i}", use_container_width=True):
                    if not guesser: st.error("Name required!")
                    else:
                        save_guess(row['Name'], n, comment, guesser)
                        st.session_state.q_idx += 1
                        st.rerun()
        else:
            st.success("All videos watched!")
            if st.button("📊 SHOW RESULTS", type="primary", use_container_width=True):
                set_state("results")
                st.rerun()

# --- MODE 3: RESULTS ---
elif current_state == "results":
    st.title("📊 Final Results")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        guesses_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()

        for i, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"Video #{i+1}")
                st.video(row['VideoPath'])
                
                video_guesses = guesses_df[guesses_df['Owner'] == row['Name']] if not guesses_df.empty else pd.DataFrame()
                if not video_guesses.empty:
                    fig = px.pie(video_guesses['Guess'].value_counts().reset_index(), 
                                 values='count', names='Guess', title="The Votes")
                    fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    for _, g in video_guesses.iterrows():
                        st.markdown(f"💬 **{g['Guesser']}**: {g['Comment']}")
                
                if st.button(f"✨ REVEAL OWNER ✨", key=f"rev_{i}", use_container_width=True):
                    st.balloons()
                    st.warning(f"THE OWNER WAS: **{row['Name']}**")

# --- FOOTER: SMALL RESET BUTTON ---
st.write("")
st.write("")
st.divider()
with st.expander("🛠️ Admin Controls"):
    st.write("Dangerous Zone - This wipes all data and returns to start.")
    if st.button("Reset & Return to Home", type="secondary", use_container_width=True):
        st.session_state.trigger_reset = True

if st.session_state.get("trigger_reset", False):
    st.error("‼️ ARE YOU SURE? This deletes all videos and submissions.")
    rc1, rc2 = st.columns(2)
    if rc1.button("🔥 YES, WIPE IT", use_container_width=True):
        full_reset()
    if rc2.button("🚫 CANCEL", use_container_width=True):
        st.session_state.trigger_reset = False
        st.rerun()
