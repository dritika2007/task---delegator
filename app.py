import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="AI Task Delegator", page_icon="🎯", layout="wide")

# --- 1. DATA INITIALIZATION ---
# This block ensures the CSV is loaded into memory ONLY ONCE.
if 'df' not in st.session_state:
    try:
        # Load from CSV initially
        st.session_state.df = pd.read_csv('team_skills_database.csv')
    except FileNotFoundError:
        st.error("Database file 'team_skills_database.csv' not found.")
        st.stop()

def delegate_task(worker_name):
    """Updates the workload directly in the Session State memory."""
    # Find the specific row index
    idx = st.session_state.df.index[st.session_state.df['name'] == worker_name].tolist()[0]
    
    if st.session_state.df.at[idx, 'load'] < 10:
        # Update the value in Session State memory
        st.session_state.df.at[idx, 'load'] += 1
        
        # Optional: Attempt to save to disk (works locally, might fail on Cloud)
        try:
            st.session_state.df.to_csv('team_skills_database.csv', index=False)
        except:
            pass 
            
        st.toast(f"✅ Delegated to {worker_name}!", icon="🚀")
        return True
    else:
        st.error(f"Cannot delegate: {worker_name} is at maximum capacity!")
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
    
    task_input = st.text_area(
        "Describe the task:",
        value=common_tasks[selected_template],
        height=150
    )
    
    # We use a button to trigger the search, but the results should persist
    find_button = st.button("🚀 Optimize & Find Workers", use_container_width=True)

with col2:
    st.subheader("Step 2: Recommended Talent")
    
    # We want results to stay visible even after a 'Delegate' click (which triggers a rerun)
    # So we check if the button was clicked OR if we are already in a "searching" state
    if find_button or task_input:
        
        # --- 3. SCORING LOGIC ---
        def calculate_score(row):
            score = 0
            worker_skills = [s.strip().lower() for s in str(row['skills']).split(',')]
            for skill in worker_skills:
                if skill in task_input.lower():
                    score += 10
            
            avail_map = {"High": 5, "Medium": 2, "Low": 0, "None": -10}
            score += avail_map.get(row['availability'], 0)
            score -= (row['load'] * 0.5)
            return score

        # IMPORTANT: Always pull from st.session_state.df to see updates!
        df_scored = st.session_state.df.copy()
        df_scored['match_score'] = df_scored.apply(calculate_score, axis=1)
        
        top_matches = df_scored.sort_values(by='match_score', ascending=False).head(3)

        for _, worker in top_matches.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {worker['name']}")
                    st.write(f"Workload: **{int(worker['load'])}/10**")
                    st.progress(min(int(worker['load']) * 10, 100))
                
                with c2:
                    if st.button("Delegate", key=f"btn_{worker['name']}"):
                        if delegate_task(worker['name']):
                            st.rerun()

# --- 4. TEAM OVERVIEW ---
# This will now reflect the 'Maya Patel' update immediately
with st.expander("📊 View Entire Team Current Load"):
    st.table(st.session_state.df[['name', 'role', 'load']])
