import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="AI Task Delegator", page_icon="💼", layout="wide")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('team_skills_database.csv')

df = load_data()

# --- NEW: Common Office Task Templates ---
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

st.title("💼 Smart Task Delegator")

col1, col2 = st.columns([2, 1.5]) # Slightly widened col2 for better readability

with col1:
    st.subheader("Define the Task")
    
    # Dropdown for common tasks
    selected_template = st.selectbox(
        "Choose a common task template (Optional):", 
        options=list(common_tasks.keys())
    )
    
    # The text area will now auto-fill based on the dropdown selection
    task_input = st.text_area(
        "Describe the task:",
        value=common_tasks[selected_template],
        placeholder="Or type specific details here...",
        height=150
    )

    if st.button("👤 Find Suitable Workers", use_container_width=True):
        if task_input:
            # --- MATCHING LOGIC ---
            def calculate_score(row):
                score = 0
                worker_skills = [s.strip().lower() for s in str(row['skills']).split(',')]
                # Higher weight for matching words in the description
                for skill in worker_skills:
                    if skill in task_input.lower():
                        score += 10
                
                avail_map = {"High": 5, "Medium": 2, "Low": 0, "None": -10}
                score += avail_map.get(row['availability'], 0)
                score -= (row['load'] * 0.5)
                return score

            df['match_score'] = df.apply(calculate_score, axis=1)
            
            # --- UPDATED: Get Top 3 matches instead of just 1 ---
            top_matches = df.sort_values(by='match_score', ascending=False).head(3)

            with col2:
                st.subheader("Top Recommendations")
                
                for i, match in top_matches.iterrows():
                    # Using a container for each recommendation to look clean
                    with st.container():
                        st.write(f"### {match['name']}")
                        st.write(f"**Role:** {match['role']}")
                        st.write(f"**Skills:** {match['skills']}")
                        
                        # Calculate progress (capped at 100)
                        load_val = min(int(match['load']) * 10, 100)
                        st.progress(load_val)
                        st.write(f"Workload: {match['load']}/10")
                        st.divider() # Adds a line between recommendations
        else:
            st.error("Please enter or select a task.")
