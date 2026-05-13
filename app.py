import streamlit as st
import pandas as pd
from thefuzz import fuzz # You may need to: pip install thefuzz

# Page Config
st.set_page_config(page_title="AI Task Delegator", page_icon="🎯", layout="wide")

# --- 1. INITIALIZATION ---
if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv('team_skills_database.csv')
    except FileNotFoundError:
        st.error("Database file 'team_skills_database.csv' not found.")
        st.stop()

# Track assignments as a list of dictionaries: {'worker': 'name', 'task': 'text'}
if 'assignments' not in st.session_state:
    st.session_state.assignments = []

def delegate_task(worker_name, task_text):
    idx = st.session_state.df.index[st.session_state.df['name'] == worker_name].tolist()[0]
    
    if st.session_state.df.at[idx, 'load'] < 10:
        st.session_state.df.at[idx, 'load'] += 1
        
        # Log the worker name and the full task text
        st.session_state.assignments.append({'worker': worker_name, 'task': task_text})
        
        try:
            st.session_state.df.to_csv('team_skills_database.csv', index=False)
        except:
            pass
            
        st.toast(f"✅ Assigned to {worker_name}!", icon="🚀")
        return True
    return False

# --- 2. UI LAYOUT ---
st.title("🎯 Smart Task Delegator")

common_tasks = {
    "Custom (Type your own)": "",
    "Frontend Update": "Update the landing page UI using React and Tailwind. Fix mobile responsiveness.",
    "Data Analysis": "Analyze monthly sales using Python and SQL. Create summary report in Tableau.",
    "Cloud Migration": "Move legacy database to AWS and set up Docker container for backend.",
}

col1, col2 = st.columns([1.5, 2])

with col1:
    st.subheader("Step 1: Define the Task")
    selected_template = st.selectbox("Choose a template:", options=list(common_tasks.keys()))
    task_input = st.text_area("Describe the task:", value=common_tasks[selected_template], height=150)
    find_button = st.button("🚀 Optimize & Find Workers", use_container_width=True)

with col2:
    st.subheader("Step 2: Recommended Talent")
    
    if find_button or task_input:
        def calculate_score(row):
            score = 0
            worker_skills = [s.strip().lower() for s in str(row['skills']).split(',')]
            for skill in worker_skills:
                if skill in task_input.lower(): score += 10
            avail_map = {"High": 5, "Medium": 2, "Low": 0, "None": -10}
            score += avail_map.get(row['availability'], 0)
            score -= (row['load'] * 0.5)
            return score

        df_scored = st.session_state.df.copy()
        df_scored['match_score'] = df_scored.apply(calculate_score, axis=1)
        top_matches = df_scored.sort_values(by='match_score', ascending=False).head(3)

        for _, worker in top_matches.iterrows():
            # --- FUZZY SAFETY CHECK ---
            is_similar = False
            highest_ratio = 0
            
            # Check current task against all previous tasks for THIS worker
            worker_history = [a['task'] for a in st.session_state.assignments if a['worker'] == worker['name']]
            
            for past_task in worker_history:
                similarity = fuzz.token_set_ratio(task_input, past_task)
                if similarity > 80: # Threshold for "Similar"
                    is_similar = True
                    highest_ratio = similarity
                    break

            with st.container(border=True):
                c1, c2 = st.columns([3, 1.5])
                with c1:
                    st.markdown(f"### {worker['name']}")
                    st.write(f"Workload: **{int(worker['load'])}/10**")
                    st.progress(min(int(worker['load']) * 10, 100))
                
                with c2:
                    if is_similar:
                        st.warning(f"⚠️ Similar Task Detected ({highest_ratio}%)")
                        if st.button("Delegate Anyway", key=f"force_{worker['name']}"):
                            if delegate_task(worker['name'], task_input):
                                st.rerun()
                    else:
                        if st.button("Delegate", key=f"btn_{worker['name']}", use_container_width=True):
                            if delegate_task(worker['name'], task_input):
                                st.rerun()

# --- 3. TEAM OVERVIEW ---
with st.expander("📊 View Entire Team Current Load"):
    st.table(st.session_state.df[['name', 'role', 'load']])
