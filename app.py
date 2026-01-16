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

def save_all_guesses(df_results, guesser_name):
    if os.path.exists(GUESS_FILE):
        existing = pd.read_csv(GUESS_FILE)
        existing = existing[existing['Guesser'] != guesser_name]
        updated = pd.concat([existing, df_results], ignore_index=True)
    else: updated = df_results
    updated.to_csv(GUESS_FILE, index=False)

# --- UI Setup ---
st.set_page_config(page_title="GLIZZY GUESS WHO", page_icon="🌭", layout="centered")

st.markdown("""
    <style>
    .header-bar { background-color: #FF4B4B; color: white; text-align: center; padding: 10px 0px; border-bottom: 5px solid #9d0208; margin: -10px -20px 20px -20px; width: calc(100% + 40px); }
    .header-title { font-size: 26px; font-weight: 900; text-transform: uppercase; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, -2px 2px 0 #000; }
    div.stForm [data-testid="stFormSubmitButton"] button { background-color: #28a745 !important; color: white !important; font-weight: bold !important; width: 100%; border: none; }
    .stButton > button { height: 3.5em; font-size: 18px !important; border-radius: 10px; transition: none !important; }
    div[data-testid="stButton"] button[kind="primary"] { background-color: #FF4B4B !important; color: white !important; border: 2px solid #9d0208 !important; }
    </style>
    <div class="header-bar"><div class="header-title">🌭 GLIZZY GUESS WHO 🌭</div></div>
    """, unsafe_allow_html=True)

current_state, shared_seed = get_state()
sub_df = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame()
submission_count = len(sub_df)

try:
    if current_state == "submitting":
        st.metric("Total Glizzies Submitted", submission_count)
        
        if submission_count > 0:
            names_display = []
            for i, name in enumerate(sub_df['Name']):
                suffix = " 👑 (Host)" if i == 0 else ""
                names_display.append(f"**{name}**{suffix}")
            st.write(f"**Players in lobby:** {', '.join(names_display)}")

        if st.session_state.get('submitted', False):
            st.success("🎉 Submission received!")
            is_host = (sub_df.iloc[0]['Name'] == st.session_state.get('my_name', ''))
            if is_host:
                st.info("👑 **You are the host.** Wait for everyone to join, then click Create the Quiz.")
                if st.button("🚀 CREATE THE QUIZ", type="primary", use_container_width=True):
                    set_state("quiz", int(time.time())); st.rerun()
            else: 
                st.info("⌛ **Please wait for the host to start the quiz.**")
            time.sleep(3); st.rerun()
        else:
            with st.form("sub_form", clear_on_submit=True):
                name = st.text_input("Your Name")
                # Updated Label Here
                file = st.file_uploader("Upload", type=["mp4", "mov", "jpg", "jpeg", "png"])
                if st.form_submit_button("SUBMIT"):
                    if name and file:
                        st.session_state.my_name = name
                        save_submission(name, file); st.session_state.submitted = True; st.rerun()
        
        with st.expander("🛠️ Admin / Reset"):
            if st.button("Reset Entire Game"): st.session_state.wants_reset = True

    elif current_state == "quiz":
        if 'shuffled_df' not in st.session_state:
            st.session_state.shuffled_df = sub_df.sample(frac=1, random_state=shared_seed).reset_index(drop=True)
            st.session_state.temp_guesses = {}
        
        df = st.session_state.shuffled_df
        guesser = st.text_input("Confirm Your Name", value=st.session_state.get('my_name', ''))
        
        for idx, row in df.iterrows():
            with st.container(border=True):
                st.write(f"### Item {idx + 1}")
                if row['Ext'] in ['jpg', 'jpeg', 'png']: st.image(row['Path'], use_container_width=True)
                else: st.video(row['Path'])
                names = sorted(sub_df['Name'].unique().tolist())
                cols = st.columns(2)
                for i, n in enumerate(names):
                    is_selected = st.session_state.temp_guesses.get(idx, {}).get('Guess') == n
                    btn_type = "primary" if is_selected else "secondary"
                    if cols[i % 2].button(n, key=f"q{idx}_{n}", use_container_width=True, type=btn_type):
                        st.session_state.temp_guesses[idx] = {'Owner': row['Name'], 'Guess': n}
                        st.rerun()
                st.text_area("Comment:", key=f"comm_{idx}", placeholder="Optional...")

        st.divider()
        if st.button("✅ SUBMIT ALL GUESSES", type="primary", use_container_width=True):
            if len(st.session_state.temp_guesses) < len(df): st.error(f"Finish all {len(df)}!")
            elif not guesser: st.error("Enter your name!")
            else:
                final_list = [[g['Owner'], g['Guess'], st.session_state.get(f"comm_{idx}", ""), guesser] for idx, g in st.session_state.temp_guesses.items()]
                save_all_guesses(pd.DataFrame(final_list, columns=["Owner", "Guess", "Comment", "Guesser"]), guesser)
                set_state("sync", shared_seed); st.rerun()

    elif current_state == "sync":
        st.header("⏳ Waiting for others...")
        guess_df = pd.read_csv(GUESS_FILE) if os.path.exists(GUESS_FILE) else pd.DataFrame()
        all_players = sub_df['Name'].unique().tolist()
        voted_players = guess_df['Guesser'].unique().tolist() if not guess_df.empty else []
        still_waiting = [p for p in all_players if p not in voted_players]
        
        st.metric("Players Finished", f"{len(voted_players)} / {submission_count}")
        st.progress(len(voted_players) / submission_count)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("✅ **Finished:**")
            for p in voted_players: st.write(f"- {p}")
        with col2:
            st.write("🏃 **Still Guessing:**")
            for p in still_waiting: st.write(f"- {p}")

        if len(voted_players) >= submission_count:
            st.success("Everyone is done! Loading results..."); time.sleep(2)
            set_state("results", shared_seed); st.rerun()
        else: time.sleep(5); st.rerun()

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
                    st.balloons(); st.warning(f"Glizzy: {row['Name']}")
        
        st.divider()
        with st.expander("🛠️ Reset"):
            if st.button("Reset Game"): st.session_state.wants_reset = True

    if st.session_state.get("wants_reset", False):
        st.error("‼️ Reset everything?"); c1, c2 = st.columns(2)
        if c1.button("🔥 YES"): full_reset()
        if c2.button("🚫 NO"): st.session_state.wants_reset = False; st.rerun()

except Exception as e: st.error(f"Error: {e}")
