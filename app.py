import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="AI Task Delegator", page_icon="🎯", layout="wide")

# --- 1. DATA PERSISTENCE & SESSION STATE ---
# We remove @st.cache_data to ensure we always interact with the live data
if 'df' not in st.session_state:
    try:
        # Initial load from the CSV file
        st.session_state.df = pd.read_csv('team_skills_database.csv')
    except FileNotFoundError:
        st.error("Database file 'team_skills_database.csv' not found. Please ensure the file exists.")
        st.stop()

def delegate_task(worker_name):
    """Updates the workload in session state and saves it to the CSV file."""
    # Find the specific row index for the worker
    idx = st.session_state.df.index[st.session_state.df['name'] == worker_name].tolist()[0]
    
    current_load = st.session_state.df.at[idx, 'load']
    
    if current_load < 10:
        # Update the value in the active Session State
        st.session_state.df.at[idx, 'load'] = current_load + 1
        
        # Save the updated DataFrame back to the CSV file immediately
        st.session_state.df.to_csv('team_skills_database.csv', index=False)
        st.toast(f"✅ Task delegated! {worker_name}'s workload is now {current_load + 1}/10", icon="🚀")
    else:
        st.error(f"Cannot delegate: {worker_name} is at maximum capacity (10/10)!")

# --- 2. TEMPLATES ---
common_tasks = {
    "Custom (Type your own)": "",
    "Frontend Update": "Update the landing page UI using React and Tailwind. Fix the mobile responsiveness issues.",
    "Data Analysis": "Analyze the monthly sales CSV using Python and SQL. Create a summary report in Tableau.",
    "Cloud Migration": "Move the legacy database to AWS and set up a Docker container for the backend.",
    "Marketing Campaign": "Write SEO-friendly copywriting for the new product launch and set up Google Ads.",
    "Security Audit": "Perform a network security pentesting and ensure SOC compliance for the new server.",
    "Document Editing": "Proofread the API Reference documentation and convert the files to Markdown.",
    "Bug Fixing": "Fix the login authentication bug in the Node.js backend and run Jest tests."
}

st.title("🎯 Smart Task Delegator")

# Layout
col1, col2 = st.columns([1.5, 2])

with col1:
    st.subheader("Step 1: Define the Task")
    selected_template = st.selectbox("Choose a template:", options=list(common_tasks.keys()))
    
    task_input = st.text_area(
        "Describe the 'Upar se' task:",
        value=common_tasks[selected_template],
        placeholder="Enter task details...",
        height=150
    )
    
    find_button = st.button("🚀 Optimize & Find Workers", use_container_width=True)

with col2:
    st.subheader("Step 2: Recommended Talent")
    
    if find_button and task_input:
        # --- 3. SCORING LOGIC (Using Session State Data) ---
        def calculate_score(row):
            score = 0
            # Ensure skills are treated as strings and handled properly
            worker_skills = [s.strip().lower() for s in str(row['skills']).split(',')]
            
            # Math: Si * ws (Skill match * 10)
            for skill in worker_skills:
                if skill in task_input.lower():
                    score += 10
            
            # Math: Ab (Availability Bonus)
            avail_map = {"High": 5, "Medium": 2, "Low": 0, "None": -10}
            score += avail_map.get(row['availability'], 0)
            
            # Math: - (L * wl) -> Load * 0.5 penalty
            score -= (row['load'] * 0.5)
            return score

        # Create a temporary scored dataframe from the current state
        df_scored = st.session_state.df.copy()
        df_scored['match_score'] = df_scored.apply(calculate_score, axis=1)
        
        # Get Top 3 matches
        top_matches = df_scored.sort_values(by='match_score', ascending=False).head(3)

        for _, worker in top_matches.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {worker['name']}")
                    st.caption(f"**Role:** {worker['role']} | **Match Score:** {worker['match_score']}")
                    st.write(f"**Skills:** {worker['skills']}")
                    
                    # Workload Visual
                    load_val = int(worker['load'])
                    st.progress(min(load_val * 10, 100)) # Ensure progress doesn't exceed 100
                    st.write(f"Workload: {load_val}/10")
                
                with c2:
                    st.write("") # Vertical alignment padding
                    # Use a unique key for every button to avoid conflicts
                    if st.button("Delegate", key=f"btn_{worker['name']}", use_container_width=True):
                        delegate_task(worker['name'])
                        st.rerun() # Forces the app to refresh and show the updated CSV values
    
    elif not task_input and find_button:
        st.warning("Please define a task first.")
    else:
        st.info("Define a task and search to see optimized talent suggestions.")

# --- 4. OPTIONAL: LIVE TEAM OVERVIEW ---
with st.expander("📊 View Entire Team Current Load"):
    # This table will update live as you click "Delegate"
    st.table(st.session_state.df[['name', 'role', 'load', 'availability']])
