import streamlit as st
import pandas as pd
import os
import time
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
        if os.path.exists(f):
            try: os.remove(f)
            except: pass
    if os.path.exists("media"):
        for f in os.listdir("media"):
            try: os.remove(os.path.join("media", f))
            except: pass
    st.session_state.clear()
    st.rerun()

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
    </style>
    <div class="header-bar">
        <div class="header-title">🌭 GLIZZY GUESS WHO 🌭</div>
    </div>
    """, unsafe_allow_html=True)

# --- EMERGENCY RESET AT TOP ---
with st.expander("🚨 RESET GAME (Admin Only)"):
    if st.button("Delete All Data & Start Over"):
        full_reset()

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
                if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
                    set_state("quiz", int(time.time()))
                    st.rerun()
            else:
                st.info("Waiting for host...")
            time.sleep(3); st.rerun()
        else:
            with st.form("sub_form"):
                name = st.text_input("Your Name")
                file = st.file_uploader("Upload Glizzy", type=["mp4", "mov", "jpg", "jpeg", "png"])
                if st.form_submit_button("SUBMIT"):
                    if name and file:
                        st.session_state.my_name = name
                        # Save logic here... (omitted for brevity, keep your existing save_submission call)
                        st.session_state.submitted = True
                        st.rerun()
            time.sleep(5); st.rerun()

    # (Keep your existing 'quiz' and 'results' logic here)

except Exception as e:
    st.error(f"Error: {e}")
