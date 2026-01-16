import streamlit as st
import pandas as pd
import os
import random
import plotly.express as px
import streamlit.components.v1 as components

# Files
DATA_FILE = "submissions.csv"
GUESS_FILE = "guesses.csv"
STATE_FILE = "game_state.txt"

# --- Helper Functions ---
def get_state():
    if not os.path.exists(STATE_FILE): return "submitting"
    with open(STATE_FILE, "r") as f: return f.read().strip()

def set_state(state):
    with open(STATE_FILE, "w") as f: f.write(state)

def save_submission(name, link):
    # Extracts the ID from the TikTok link to force a better embed
    video_id = link.split('/')[-1].split('?')[0]
    embed_url = f"https://www.tiktok.com/embed/v2/{video_id}"
    new_data = pd.DataFrame([[name, embed_url]], columns=["Name", "Link"])
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

def trigger_glitter():
    # Custom HTML/JS for falling glitter effect
    glitter_js = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script>
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FFD700', '#FF69B4', '#00E5FF', '#7FFF00']
        });
    </script>
    """
    components.html(glitter_js, height=0)

# --- UI Setup ---
st.set_page_config(page_title="The Glizzy Quiz", page_icon="🌭")
current_state = get_state()

# --- MODE 1: SUBMITTING ---
if current_state == "submitting":
    st.title("🌭 The Glizzy Quiz: Submissions")
    if os.path.exists(DATA_FILE):
        st.metric("Total Submissions", len(pd.read_csv(DATA_FILE)))

    with st.form("sub_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        link = st.text_input("TikTok Link")
        if st.form_submit_button("Submit Link"):
            if name and link:
                save_submission(name, link)
                st.success("Locked in!")
    
    if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
        set_state("quiz"); st.rerun()

# --- MODE 2: THE QUIZ ---
elif current_state == "quiz":
    st.title("🎬 Who Posted This?")
    df = pd.read_csv(DATA_FILE)
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    
    if st.session_state.q_idx < len(df):
        row = df.iloc[st.session_state.q_idx]
        # NEW TIKTOK PLAYER
        components.iframe(row['Link'], height=700)
        
        guesser = st.text_input("Your Name", key="guesser_name")
        comment = st.text_area("Why them?", placeholder="Comment here...")
        
        names = sorted(df['Name'].unique().tolist())
        cols = st.columns(2)
        for i, n in enumerate(names):
            if cols[i%2].button(n, key=f"guess_{i}", use_container_width=True):
                if not guesser: st.error("Enter your name!")
                else:
                    save_guess(row['Name'], n, comment, guesser)
                    st.session_state.q_idx += 1; st.rerun()
    else:
        st.success("Quiz finished!")
        if st.button("📊 SHOW RESULTS", type="primary", use_container_width=True):
            set_state("results"); st.rerun()

# --- MODE 3: RESULTS ---
elif current_state == "results":
    st.title("📊 Results")
    df = pd.read_csv(DATA_FILE)
    guesses_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()

    for i, row in df.iterrows():
        with st.container(border=True):
            st.subheader(f"Video #{i+1}")
            components.iframe(row['Link'], height=700)
            
            video_guesses = guesses_df[guesses_df['Owner'] == row['Name']] if not guesses_df.empty else pd.DataFrame()
            if not video_guesses.empty:
                fig = px.pie(video_guesses['Guess'].value_counts().reset_index(), values='count', names='Guess', title="Guesses")
                st.plotly_chart(fig, use_container_width=True)
                for _, g in video_guesses.iterrows():
                    st.markdown(f"💬 **{g['Guesser']}**: {g['Comment']}")
            
            if st.button(f"✨ REVEAL GLIZZY ✨", key=f"rev_{i}", use_container_width=True):
                trigger_glitter()
                st.info(f"The legend: **{row['Name']}**")

    if st.button("🧨 RESET GAME", use_container_width=True):
        for f in [DATA_FILE, GUESS_FILE, STATE_FILE]:
            if os.path.exists(f): os.remove(f)
        st.session_state.clear(); st.rerun()
