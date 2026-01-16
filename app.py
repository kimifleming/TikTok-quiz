import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px

# Files
DATA_FILE = "submissions.csv"
GUESS_FILE = "guesses.csv"
STATE_FILE = "game_state.txt"

# Ensure media directory exists
if not os.path.exists("media"):
    os.makedirs("media")

# --- Helper Functions ---
def get_state():
    if not os.path.exists(STATE_FILE): return "submitting"
    try:
        with open(STATE_FILE, "r") as f: return f.read().strip()
    except:
        return "submitting"

def set_state(state):
    with open(STATE_FILE, "w") as f: f.write(state)

def save_submission(name, uploaded_file):
    ext = uploaded_file.name.split('.')[-1]
    file_path = os.path.join("media", f"{int(time.time())}_{name}.{ext}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    new_data = pd.DataFrame([[name, file_path, ext.lower()]], columns=["Name", "Path", "Ext"])
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
    if os.path.exists("media"):
        for f in os.listdir("media"):
            try: os.remove(os.path.join("media", f))
            except: pass
    st.session_state.clear()
    st.rerun()

# --- UI Setup ---
st.set_page_config(page_title="GLIZZY GUESS WHO", page_icon="🌭", layout="centered")

# MINIMAL CSS: Header Bar only
st.markdown("""
    <style>
    .header-bar {
        background-color: #FF4B4B;
        color: white;
        text-align: center;
        padding: 10px 0px;
        border-bottom: 5px solid #9d0208;
        margin: -10px -20px 20px -20px;
        width: calc(100% + 40px);
    }
    .header-title {
        font-size: 26px;
        font-weight: 900;
        text-transform: uppercase;
        text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000;
    }
    /* Buttons in quiz/results stay tap-friendly */
    .stButton > button {
        height: 3.5em;
        font-size: 18px !important;
        border-radius: 10px;
    }
    </style>
    <div class="header-bar">
        <div class="header-title">🌭 GLIZZY GUESS WHO 🌭</div>
    </div>
    """, unsafe_allow_html=True)

# --- Global Footer Reset ---
def global_footer():
    st.write("")
    st.divider()
    with st.expander("🛠️ Admin / Reset"):
        if st.button("Reset & Return to Home", type="secondary", use_container_width=True):
            st.session_state.wants_reset = True
    
    if st.session_state.get("wants_reset", False):
        st.error("‼️ Reset everything?")
        rc1, rc2 = st.columns(2)
        if rc1.button("🔥 YES", key="g_reset_yes"): full_reset()
        if rc2.button("🚫 NO", key="g_reset_no"): 
            st.session_state.wants_reset = False
            st.rerun()

# --- MAIN APP LOGIC ---
current_state = get_state()

try:
    if current_state == "submitting":
        st.subheader("Step 1: Submissions")
        
        if st.session_state.get('submitted', False):
            st.success("✅ Submission received!")
        
        if os.path.exists(DATA_FILE):
            st.metric("Total Entrants", len(pd.read_csv(DATA_FILE)))

        # Standard Streamlit Form (No custom button CSS)
        with st.form("sub_form", clear_on_submit=True):
            name = st.text_input("Your Name", placeholder="Enter your name...")
            file = st.file_uploader("Photo or Video", type=["mp4", "mov", "jpg", "jpeg", "png"])
            st.form_submit_button("SUBMIT")

        st.write("")
        st.divider()
        st.caption("Admin Only: Start the game once everyone is done.")
        if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
            st.session_state.confirm_quiz = True
        
        if st.session_state.get("confirm_quiz", False):
            st.warning("⚠️ **Please make sure all entrants have submitted before continuing.**")
            if st.button("✅ Yes, everyone is in", use_container_width=True):
                set_state("quiz"); st.session_state.confirm_quiz = False; st.rerun()

    elif current_state == "quiz":
        st.subheader("🎬 Who is this?")
        df = pd.read_csv(DATA_FILE)
        if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
        
        if st.session_state.q_idx < len(df):
            row = df.iloc[st.session_state.q_idx]
            st.write(f"**Item {st.session_state.q_idx + 1} of {len(df)}**")
            
            if row['Ext'] in ['jpg', 'jpeg', 'png']:
                st.image(row['Path'], use_container_width=True)
            else:
                st.video(row['Path'])
            
            guesser = st.text_input("Your Name", key="guesser_name")
            comment = st.text_area("Why?", placeholder="Give us the tea...")
            
            names = sorted(df['Name'].unique().tolist())
            for i, n in enumerate(names):
                if st.button(n, key=f"g_{i}", use_container_width=True):
                    if not guesser: st.error("Name required!")
                    else:
                        save_guess(row['Name'], n, comment, guesser)
                        st.session_state.q_idx += 1; st.rerun()
        else:
            if st.button("📊 SHOW RESULTS", type="primary", use_container_width=True):
                set_state("results"); st.rerun()

    elif current_state == "results":
        st.subheader("📊 Final Results")
        df = pd.read_csv(DATA_FILE)
        guesses_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()

        for i, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"#{i+1}")
                if row['Ext'] in ['jpg', 'jpeg', 'png']:
                    st.image(row['Path'], use_container_width=True)
                else:
                    st.video(row['Path'])
                
                v_guesses = guesses_df[guesses_df['Owner'] == row['Name']] if not guesses_df.empty else pd.DataFrame()
                if not v_guesses.empty:
                    fig = px.pie(v_guesses['Guess'].value_counts().reset_index(), values='count', names='Guess')
                    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                    st.plotly_chart(fig, use_container_width=True)
                    for _, g in v_guesses.iterrows():
                        st.caption(f"💬 **{g['Guesser']}**: {g['Comment']}")
                
                if st.button(f"✨ REVEAL OWNER ✨", key=f"rev_{i}", use_container_width=True):
                    st.balloons(); st.warning(f"THE OWNER: {row['Name']}")

        if not guesses_df.empty:
            st.divider()
            st.header("🏆 Scoreboard")
            guesses_df['correct'] = (guesses_df['Owner'] == guesses_df['Guess']) & (guesses_df['Guesser'] != guesses_df['Owner'])
            leaderboard = guesses_df.groupby('Guesser')['correct'].sum().reset_index()
            leaderboard = leaderboard.sort_values(by='correct', ascending=False)
            st.table(leaderboard.rename(columns={'Guesser': 'Name', 'correct': 'Points'}).set_index('Name'))

except Exception as e:
    st.error(f"App Error: {e}")

global_footer()
