import streamlit as st
import pandas as pd

# Load your team data
df = pd.read_csv('team_skills_database.csv')

st.title("🚀 AI Task Delegator")
st.write("Paste your office task below to find the best worker.")

# Input for the task
task_input = st.text_area("What is the task coming from the 'Upar se' (Boss)?")

if st.button("Suggest Best Worker"):
    if task_input:
        # Simple logic: Check which worker has skills mentioned in the task
        # We rank them by availability and skill match
        task_keywords = task_input.lower().split()
        
        def calculate_score(row):
            score = 0
            # Match skills
            for skill in row['skills'].split(','):
                if skill.strip().lower() in task_input.lower():
                    score += 5
            # Factor in Availability
            if row['availability'] == 'High': score += 3
            elif row['availability'] == 'Medium': score += 1
            # Subtract Load
            score -= (row['load'] * 0.1)
            return score

        df['match_score'] = df.apply(calculate_score, axis=1)
        best_match = df.sort_values(by='match_score', ascending=False).iloc[0]

        st.success(f"The best person for this task is: **{best_match['name']}**")
        st.info(f"**Role:** {best_match['role']}  \n**Skills:** {best_match['skills']}  \n**Current Load:** {best_match['load']}/10")
    else:
        st.warning("Please enter a task description first.")
