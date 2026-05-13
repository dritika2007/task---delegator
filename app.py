import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="AI Task Delegator", page_icon="🎯", layout="wide")

# --- 1. DATA INITIALIZATION (The "Source of Truth" Logic) ---
# This block only runs if 'df' is NOT in the current session memory.
# A page reload (F5) wipes session memory, triggering a fresh read from the CSV.
if 'df' not in st.session_state:
    try:
        # Pull original data from the CSV file
        st.session_state.df = pd.read_csv('team_skills_database.csv')
        # Initialize an empty assignment history for this session
        st.session_state.assignments = []
    except FileNotFoundError:
        st.error("Database file 'team_skills_database.csv' not found.")
        st.stop()

def delegate_task(worker_name, task_text):
    """Updates workload in memory and attempts to persist to disk."""
    idx = st.session_state.df.index[st.session_state.df['name'] == worker_name].tolist()[0]
    
    if st.session_state.df.at[idx, 'load'] < 10:
        # 1. Update the 'Current State' (Session memory)
        st.session_state.df.at[idx, 'load'] += 1
        
        # 2. Log the task to the history to prevent duplicates in THIS session
        st.session_state.assignments.append({'worker': worker_name, 'task': task_text})
        
        # 3. Update the 'Original CSV' (Disk)
        # Note: On Streamlit Cloud, this file resets on app sleep, but stays during active use.
        try:
            st.session_state.df.to_csv('team_skills_database.csv', index=False)
        except Exception as e:
            pass # Silent fail if disk is read-only
            
        st.toast(f"✅ Delegated to {worker_name}!", icon="🚀")
        return True
    return False

# --- 2. UI & SEARCH LOGIC ---
st.title("🎯 Smart Task Delegator")

common_tasks = {
    "Custom (Type your own)": "",
    "Frontend Update": "Update the landing page UI using React and Tailwind. Fix mobile responsiveness.",
    "Data Analysis": "Analyze monthly sales using Python and SQL. Create summary report in Tableau.",
}

col1, col2 = st.columns([1.5, 2])

with col1:
    st.subheader("Step 1: Define the Task")
    selected_template = st.selectbox("Template:", options=list(common_tasks.keys()))
    task_input = st.text_area("Task Description:", value=common_tasks[selected_template], height=150)
    find_button = st.button("🚀 Find & Optimize", use_container_width=True)

with col2:
    st.subheader("Step 2: Recommended Talent")
    
    if find_button or task_input:
        # SCORING LOGIC - Pulls data from st.session_state.df (The 'Current State')
        def calculate_score(row):
            score = 0
            worker_skills = [s.strip().lower() for s in str(row['skills']).split(',')]
            for skill in worker_skills:
                if skill in task_input.lower(): score += 10
            
            avail_map = {"High": 5, "Medium": 2, "Low": 0, "None": -10}
            score += avail_map.get(row['availability'], 0)
            score -= (row['load'] * 0.5) # Penalty based on 'Current State' load
            return score

        # Always work with the live session data
        df_current = st.session_state.df.copy()
        df_current['match_score'] = df_current.apply(calculate_score, axis=1)
        top_matches = df_current.sort_values(by='match_score', ascending=False).head(3)

        for _, worker in top_matches.iterrows():
            # --- OVERLAP SAFETY CHECK ---
            is_similar = False
            current_words = set(task_input.lower().split())
            worker_history = [a['task'] for a in st.session_state.assignments if a['worker'] == worker['name']]

            for past_task in worker_history:
                past_words = set(past_task.lower().split())
                overlap = len(current_words.intersection(past_words)) / len(current_words) if current_words else 0
                if overlap > 0.7:
                    is_similar = True
                    break

            with st.container(border=True):
                c1, c2 = st.columns([3, 1.5])
                with c1:
                    st.markdown(f"### {worker['name']}")
                    st.write(f"Workload: **{int(worker['load'])}/10**")
                    st.progress(min(int(worker['load']) * 10, 100))
                
                with c2:
                    if is_similar:
                        st.warning("⚠️ Similar Task")
                        if st.button("Force Delegate", key=f"f_{worker['name']}"):
                            if delegate_task(worker['name'], task_input): st.rerun()
                    else:
                        if st.button("Delegate", key=f"d_{worker['name']}"):
                            if delegate_task(worker['name'], task_input): st.rerun()

# --- 3. TEAM OVERVIEW ---
with st.expander("📊 Live Team Workload (Current Session State)"):
    st.table(st.session_state.df[['name', 'role', 'load']])
