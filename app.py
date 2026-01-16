import streamlit as st
import pandas as pd
import os
import time
import random
import plotly.express as px

# Files
DATA_FILE = "submissions.csv"
GUESS_FILE = "guesses.csv"
STATE_FILE = "game_state.txt"

if not os.path.exists("media"):
    os.makedirs("media")

# --- Helper Functions ---
def get_state():
    if not os.path.exists(STATE_FILE): return "submitting", 0
    try:
        with open(STATE_FILE, "r") as f:
            parts = f.read().strip().split('|')
            return parts[0], (int(parts[1]) if len(parts) > 1 else 0)
    except: return "submitting", 0

def set_state(state, seed=0):
    with open(STATE_FILE, "w") as f:
        f.write(f"{state}|{seed}")

def full_reset():
    for f in [DATA_FILE, GUESS_FILE, STATE_FILE]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists("media"):
        for f in os.listdir("media"):
            try: os.remove(os.path.join("media", f))
            except: pass
    st.session_state.clear()
    st.rerun()

def save_submission(name, uploaded_file):
    ext = uploaded_file.name.split('.')[-1]
    file_path = os.path.join("media", f"{int(time.time())}_{name}.{ext}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    new_data = pd.DataFrame([[name, file_path, ext.lower()]], columns=["Name", "Path", "Ext"])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else: df = new_data
    df.to_csv(DATA_FILE, index=False)

def save_guess(video_owner, guessed_name, comment, guesser_name):
    clean_comment = ""
    if pd.notna(comment) and str(comment).strip().lower() != "nan" and str(comment).strip() != "":
        clean_comment = str(comment).strip()
    new_guess = pd.DataFrame([[video_owner, guessed_name, clean_comment, guesser_name]], 
                             columns=["Owner", "Guess", "Comment", "Guesser"])
    if os.path.exists(GUESS_FILE):
        df = pd.read_csv(GUESS_FILE)
        df = pd.concat([df, new_guess], ignore_index=True)
    else: df = new_guess
    df.to_csv(GUESS_FILE, index=False)

# --- UI Setup ---
st.set_page_config(page_title="GLIZZY GUESS WHO", page_icon="🌭", layout="centered")

st.markdown("""
    <style>
    .header-bar {
        background-color: #FF4B4B; color: white; text-align: center;
        padding: 10px 0px; border-bottom: 5px solid #9d0208;
        margin: -10px -20px 20px -20px; width: calc(100% + 40px);
    }
    .header-title {
        font-size: 26px; font-weight: 900; text-transform: uppercase;
        text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, -2px 2px 0 #000;
    }
    div.stForm [data-testid="stFormSubmitButton"] button {
        background-color: #28a745 !important; color: white !important;
        font-weight: bold !important; width: 100%;
    }
    .stButton > button { height: 3.5em; font-size: 18px !important; border-radius: 10px; }
    .stButton > button:focus, .stButton > button:active {
        background-color: #702963 !important; color: white !important;
        border: 2px solid #4B0082 !important;
    }
    /* Style for the small reset button at bottom */
    .reset-btn-container { margin-top: 50px; }
    </style>
    <div class="header-bar">
        <div class="header-title">🌭 GLIZZY GUESS WHO 🌭</div>
    </div>
    """, unsafe_allow_html=True)

# --- Global Footer Logic ---
def global_footer():
    st.write("---")
    if not st.session_state.get("confirm_reset_all", False):
        if st.button("🗑️ Reset Game", key="main_reset_btn", type="secondary", use_container_width=False):
            st.session_state.confirm_reset_all = True
            st.rerun()
    else:
        st.error("‼️ **Reset everything for everyone?**")
        c1, c2 = st.columns(2)
        if c1.button("🔥 YES", use_container_width=True):
            full_reset()
        if c2.button("🚫 NO", use_container_width=True):
            st.session_state.confirm_reset_all = False
            st.rerun()

# --- Main Flow ---
current_state, shared_seed = get_state()
sub_df = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame()
submission_count = len(sub_df)

try:
    if current_state == "submitting":
        st.metric("Total Glizzies Submitted", submission_count)
        
        if submission_count > 0:
            st.write(f"**Players ready:** {', '.join(sub_df['Name'].tolist())}")

        if st.session_state.get('submitted', False):
            st.success("🎉 Submission received!")
            is_host = (sub_df.iloc[0]['Name'] == st.session_state.get('my_name', ''))
            
            if is_host:
                st.info("👑 You are the Host. Wait for everyone, then start.")
                if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
                    set_state("quiz", int(time.time()))
                    st.rerun()
            else:
                st.info("Waiting for the host to start the quiz...")
            time.sleep(3); st.rerun()
        else:
            with st.form("sub_form", clear_on_submit=True):
                name = st.text_input("Your Name")
                file = st.file_uploader("Upload Glizzy", type=["mp4", "mov", "jpg", "jpeg", "png"])
                if st.form_submit_button("SUBMIT"):
                    if name and file:
                        st.session_state.my_name = name
                        save_submission(name, file)
                        st.session_state.submitted = True
                        st.rerun()
            time.sleep(5); st.rerun()

    elif current_state == "quiz":
        if 'shuffled_df' not in st.session_state:
            st.session_state.shuffled_df = sub_df.sample(frac=1, random_state=shared_seed).reset_index(drop=True)
            st.session_state.q_idx = 0
        
        df = st.session_state.shuffled_df
        if st.session_state.q_idx < len(df):
            row = df.iloc[st.session_state.q_idx]
            st.write(f"**Item {st.session_state.q_idx + 1} of {len(df)}**")
            if row['Ext'] in ['jpg', 'jpeg', 'png']: st.image(row['Path'], use_container_width=True)
            else: st.video(row['Path'])
            
            st.write("### **Guess who it is:**")
            guesser = st.text_input("Your Name", value=st.session_state.get('persistent_guesser', st.session_state.get('my_name', '')), key="guesser_input")

            names = sorted(sub_df['Name'].unique().tolist())
            for i, n in enumerate(names):
                if st.button(n, key=f"g_{i}", use_container_width=True):
                    if not guesser: st.error("Enter name first!")
                    else:
                        st.session_state.persistent_guesser = guesser
                        comm_val = st.session_state.get(f"temp_comm_{st.session_state.q_idx}", "")
                        save_guess(row['Name'], n, comm_val, guesser)
                        time.sleep(0.3); st.session_state.q_idx += 1; st.rerun()
            st.text_area("Optional Comment:", key=f"temp_comm_{st.session_state.q_idx}")
        else:
            guess_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()
            total_required = submission_count * submission_count
            if len(guess_df) < total_required:
                st.warning(f"Waiting for others... ({len(guess_df)} / {total_required})")
                time.sleep(3); st.rerun()
            else:
                if st.button("📊 SHOW RESULTS", type="primary", use_container_width=True):
                    set_state("results", shared_seed); st.rerun()

    elif current_state == "results":
        st.subheader("📊 Final Results")
        df = sub_df.sample(frac=1, random_state=shared_seed).reset_index(drop=True)
        guesses_df = pd.read_csv(GUESS_FILE)
        for i, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"#{i+1}")
                if row['Ext'] in ['jpg', 'jpeg', 'png']: st.image(row['Path'], use_container_width=True)
                else: st.video(row['Path'])
                v_guesses = guesses_df[guesses_df['Owner'] == row['Name']]
                fig = px.pie(v_guesses['Guess'].value_counts().reset_index(), values='count', names='Guess')
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                st.plotly_chart(fig, use_container_width=True)
                for _, g in v_guesses.iterrows():
                    c = str(g['Comment']).strip()
                    if c and c.lower() != "nan": st.caption(f"💬 **{g['Guesser']}**: {c}")
                if st.button(f"✨ REVEAL ✨", key=f"rev_{i}", use_container_width=True):
                    st.balloons(); st.warning(f"THE OWNER: {row['Name']}")
        
        st.divider()
        st.header("🏆 Scoreboard")
        guesses_df['correct'] = (guesses_df['Owner'] == guesses_df['Guess'])
        leaderboard = guesses_df.groupby('Guesser')['correct'].sum().reset_index()
        leaderboard['Score'] = leaderboard['correct'].astype(str) + " / " + str(submission_count)
        st.table(leaderboard[['Guesser', 'Score']].sort_values(by='correct', ascending=False).set_index('Guesser'))

except Exception as e:
    st.error(f"Error: {e}")

global_footer()
