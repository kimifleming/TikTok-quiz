import streamlit as st
import pandas as pd
import os
import random
import plotly.express as px

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
    clean_link = link.split('?')[0] 
    new_data = pd.DataFrame([[name, clean_link]], columns=["Name", "Link"])
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

# --- UI Setup ---
st.set_page_config(page_title="The Glizzy Quiz", page_icon="🌭", layout="centered")
current_state = get_state()

# --- MODE 1: SUBMITTING ---
if current_state == "submitting":
    st.title("🌭 The Glizzy Quiz: Submissions")
    
    # Count submissions
    if os.path.exists(DATA_FILE):
        count = len(pd.read_csv(DATA_FILE))
        st.metric("Total Submissions", count)

    with st.form("sub_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        link = st.text_input("TikTok Link")
        if st.form_submit_button("Submit Link"):
            if name and link:
                save_submission(name, link)
                st.success(f"Locked in, {name}!")
            else:
                st.error("Fill out both fields!")
    
    st.divider()
    if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
        set_state("quiz")
        st.rerun()

# --- MODE 2: THE QUIZ ---
elif current_state == "quiz":
    st.title("🎬 Who Posted This?")
    if not os.path.exists(DATA_FILE):
        st.warning("No data found.")
        if st.button("Back to start"): set_state("submitting"); st.rerun()
    else:
        df = pd.read_csv(DATA_FILE)
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        
        if st.session_state.q_idx < len(df):
            row = df.iloc[st.session_state.q_idx]
            st.progress(st.session_state.q_idx / len(df))
            st.video(row['Link'])
            
            st.write("### Your Info")
            guesser = st.text_input("Your Name (So we know who's talking)", key="guesser_name")
            comment = st.text_area("Optional: Why did you pick them?", placeholder="I recognize that bedroom wall...")
            
            st.write("### Guess the owner:")
            names = sorted(df['Name'].unique().tolist())
            cols = st.columns(2)
            for i, n in enumerate(names):
                if cols[i%2].button(n, key=f"guess_{i}", use_container_width=True):
                    if not guesser:
                        st.error("Please enter your name first!")
                    else:
                        save_guess(row['Name'], n, comment, guesser)
                        st.session_state.q_idx += 1
                        st.rerun()
        else:
            st.balloons()
            st.success("All videos watched!")
            if st.button("📊 SHOW RESULTS FOR EVERYONE", type="primary", use_container_width=True):
                set_state("results")
                st.rerun()

# --- MODE 3: RESULTS ---
elif current_state == "results":
    st.title("📊 The Final Results")
    df = pd.read_csv(DATA_FILE)
    guesses_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()

    for i, row in df.iterrows():
        with st.container(border=True):
            st.subheader(f"Video #{i+1}")
            st.video(row['Link'])
            
            # Filter guesses for this specific video
            video_guesses = guesses_df[guesses_df['Owner'] == row['Name']] if not guesses_df.empty else pd.DataFrame()
            
            # Pie Chart
            if not video_guesses.empty:
                counts = video_guesses['Guess'].value_counts().reset_index()
                counts.columns = ['Name', 'Votes']
                fig = px.pie(counts, values='Votes', names='Name', title="The Group's Guesses")
                st.plotly_chart(fig, use_container_width=True)
                
                # Comments Section
                st.write("**What everyone said:**")
                for _, g in video_guesses.iterrows():
                    if pd.notna(g['Comment']) and g['Comment'].strip() != "":
                        st.markdown(f"💬 **{g['Guesser']}** (guessed {g['Guess']}): *\"{g['Comment']}\"*")
                    else:
                        st.markdown(f"👤 **{g['Guesser']}** guessed {g['Guess']} (No comment)")
            
            st.write("") # Spacer
            if st.button(f"✨ REVEAL GLIZZY ✨", key=f"rev_{i}", use_container_width=True):
                st.balloons()
                st.info(f"The legend who posted this was: **{row['Name']}**")

    st.divider()
    if st.button("🧨 RESET GAME FOR EVERYONE", use_container_width=True):
        for f in [DATA_FILE, GUESS_FILE, STATE_FILE]:
            if os.path.exists(f): os.remove(f)
        st.session_state.clear()
        st.rerun()
