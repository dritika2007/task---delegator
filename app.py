import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="AI Task Delegator", page_icon="🎯", layout="wide")

# --- DATA PERSISTENCE LAYER ---
# We use session_state to keep the workload updates "alive" during the app session
if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv('team_skills_database.csv')
    except FileNotFoundError:
        # Fallback if file isn't found
        st.error("Database file 'team_skills_database.csv' not found.")
        st.stop()

def delegate_task(worker_name):
    """Increments the workload for a specific worker."""
    # Find the row and increment load (max cap at 10)
    idx = st.session_state.df.index[st.session_state.df['name'] == worker_name].tolist()[0]
    if st.session_state.df.at[idx, 'load'] < 10:
        st.session_state.df.at[idx, 'load'] += 1
        # Save back to CSV to persist changes
        st.session_state.df.to_csv('team_skills_database.csv', index=False)
        st.toast(f"✅ Task delegated! {worker_name}'s workload updated.", icon="🚀")
    else:
        st.error(f"Cannot delegate: {worker_name} is at maximum capacity!")

# --- TEMPLATES ---
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
    selected_template = st.selectbox("Template:", options=list(common_tasks.keys()))
    
    task_input = st.text_area(
        "Describe the 'Upar se' task:",
        value=common_tasks[selected_template],
        height=150
    )
    
    find_button = st.button("🚀 Optimize & Find Workers", use_container_width=True)

with col2:
    st.subheader("Step 2: Recommended Talent")
    
    if find_button and task_input:
        # --- IMPROVED SCORING LOGIC ---
        def calculate_score(row):
            score = 0
            worker_skills = [s.strip().lower() for s in str(row['skills']).split(',')]
            for skill in worker_skills:
                if skill in task_input.lower():
                    score += 10
            
            avail_map = {"High": 5, "Medium": 2, "Low": 0, "None": -10}
            score += avail_map.get(row['availability'], 0)
            score -= (row['load'] * 0.5) # Penalty for high workload
            return score

        # Apply scoring to current session state data
        df_scored = st.session_state.df.copy()
        df_scored['match_score'] = df_scored.apply(calculate_score, axis=1)
        
        # Suggest Top 3 workers to optimize distribution
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
                    st.progress(load_val * 10)
                    st.write(f"Workload: {load_val}/10")
                
                with c2:
                    st.write("") # Padding
                    if st.button("Delegate", key=f"btn_{worker['name']}", use_container_width=True):
                        delegate_task(worker['name'])
                        st.rerun() # Refresh to update scores and progress bars
    elif not task_input and find_button:
        st.warning("Please define a task first.")
    else:
        st.info("Select a task and click search to see optimized suggestions.")

# --- PERSISTENT TEAM VIEW (Optional) ---
with st.expander("📊 View Entire Team Load"):
    st.dataframe(st.session_state.df, use_container_width=True)
