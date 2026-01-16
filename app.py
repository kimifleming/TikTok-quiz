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
    new_data = pd.DataFrame([[name, link]], columns=["Name", "Link"])
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

# This function now uses a more reliable "Key" system to fire the JS
def trigger_hotdog_confetti(key):
    hotdog_js = f"""
    <div id="confetti-trigger-{key}">
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
        <script>
            var end = Date.now() + (2 * 1000);
            var scalar = 3.5;
            var hotdog = confetti.shapeFromText({{ text: '🌭', scalar: scalar }});

            (function frame() {{
              confetti({{
                particleCount: 40,
                angle: 60,
                spread: 55,
                origin: {{ x: 0, y: 0.2 }},
                shapes: [hotdog],
                scalar: scalar
              }});
              confetti({{
                particleCount: 40,
                angle: 120,
                spread: 55,
                origin: {{ x: 1, y: 0.2 }},
                shapes: [hotdog],
                scalar: scalar
              }});

              if (Date.now() < end) {{
                requestAnimationFrame(frame);
              }}
            }}());
        </script>
    </div>
    """
    components.html(hotdog_js, height=0)

# --- UI Setup ---
st.set_page_config(page_title="The Glizzy Quiz", page_icon="🌭")
current_state = get_state()

if current_state == "submitting":
    st.title("🌭 Step 1: Submissions")
    if os.path.exists(DATA_FILE):
        st.metric("TikToks Collected", len(pd.read_csv(DATA_FILE)))

    with st.form("sub_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        link = st.text_input("Paste TikTok Link")
        if st.form_submit_button("Submit Link"):
            if name and link:
                save_submission(name, link)
                st.success("Successfully added!")
    
    st.divider()
    if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
        set_state("quiz"); st.rerun()

elif current_state == "quiz":
    st.title("🎬 Guess the Creator")
    df = pd.read_csv(DATA_FILE)
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    
    if st.session_state.q_idx < len(df):
        row = df.iloc[st.session_state.q_idx]
        st.write(f"**Video {st.session_state.q_idx + 1} of {len(df)}**")
        
        st.info("Watch the video, then return here to vote!")
        st.link_button("🔥 WATCH TIKTOK 🔥", row['Link'], use_container_width=True)
        
        st.divider()
        guesser = st.text_input("Your Name", key="guesser_name")
        comment = st.text_area("Your Comment", placeholder="Why them?")
        
        names = sorted(df['Name'].unique().tolist())
        cols = st.columns(2)
        for i, n in enumerate(names):
            if cols[i%2].button(n, key=f"guess_{i}", use_container_width=True):
                if not guesser: st.error("Please enter your name first!")
                else:
                    save_guess(row['Name'], n, comment, guesser)
                    st.session_state.q_idx += 1; st.rerun()
    else:
        st.success("All videos watched!")
        if st.button("📊 SHOW RESULTS", type="primary", use_container_width=True):
            set_state("results"); st.rerun()

elif current_state == "results":
    st.title("📊 Final Results")
    df = pd.read_csv(DATA_FILE)
    guesses_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()

    for i, row in df.iterrows():
        # Using a session state check to trigger confetti for each specific reveal
        reveal_key = f"revealed_{i}"
        if reveal_key not in st.session_state:
            st.session_state[reveal_key] = False

        with st.container(border=True):
            st.subheader(f"Video #{i+1}")
            st.link_button("📺 Re-watch Video", row['Link'])
            
            video_guesses = guesses_df[guesses_df['Owner'] == row['Name']] if not guesses_df.empty else pd.DataFrame()
            if not video_guesses.empty:
                fig = px.pie(video_guesses['Guess'].value_counts().reset_index(), values='count', names='Guess', title="The Votes")
                st.plotly_chart(fig, use_container_width=True)
                for _, g in video_guesses.iterrows():
                    st.markdown(f"💬 **{g['Guesser']}**: {g['Comment']}")
            
            if st.button(f"✨ REVEAL GLIZZY ✨", key=f"rev_{i}", use_container_width=True):
                st.session_state[reveal_key] = True

            if st.session_state[reveal_key]:
                trigger_hotdog_confetti(i) # Triggered separately to ensure it loads
                st.warning(f"THE OWNER WAS: **{row['Name']}**")

    if st.button("🧨 RESET GAME", use_container_width=True):
        for f in [DATA_FILE, GUESS_FILE, STATE_FILE]:
            if os.path.exists(f): os.remove(f)
        st.session_state.clear(); st.rerun()
