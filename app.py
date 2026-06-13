import streamlit as st
import pandas as pd
import numpy as np
import time

# Page Configuration
st.set_page_config(
    page_title="Cognitive Talent Engine - Intelligent Candidate Discovery",
    page_icon="🚀",
    layout="wide"
)

# Title & Description
st.title("🚀 Cognitive Talent Engine")
st.subheader("Intelligent Candidate Discovery & Semantic Ranking Engine")
st.write(
    "Traditional ATS fails due to the 'Keyword Fallacy'. This platform intelligently segments resumes, "
    "calculates **Career Velocity**, maps **Skill Adjacency**, and provides **Explainable AI (XAI)** reasoning."
)

st.markdown("---")

# Layout Split: Left for JD Input, Right for System Configurations
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📄 Step 1: Input Job Description (JD)")
    jd_input = st.text_area(
        "Paste the complex, nuanced job requirements here:",
        placeholder="e.g., Looking for a Senior MLOps Engineer with 4+ years of experience in distributed training pipelines using PyTorch. Experience with Kubernetes and low-latency model serving is highly desired...",
        height=180
    )

with col_right:
    st.markdown("### ⚙️ Step 2: Fine-Tune Dynamic Weights")
    st.caption("Adjust priorities based on role urgency and seniority:")
    
    w_semantic = st.slider("Semantic Match Weight (w₁)", 0.0, 1.0, 0.50, step=0.05)
    w_velocity = st.slider("Career Velocity Weight (w₂)", 0.0, 1.0, 0.30, step=0.05)
    w_recency = st.slider("Skill Recency Weight (w₃)", 0.0, 1.0, 0.20, step=0.05)
    
    # Validation check for weights summing to 1.0
    total_w = w_semantic + w_velocity + w_recency
    if round(total_w, 2) != 1.0:
        st.warning(f"⚠️ Total weight is {total_w:.2f}. For ideal scoring, weights should sum to 1.0.")
    else:
        st.success("✅ Weights configuration is mathematically optimized.")

# Mock Candidate Data Pipeline for PoC Showcase
def generate_mock_shortlist(jd_text):
    candidates = [
        {
            "Rank": 1,
            "Candidate_ID": "CAND_042",
            "Semantic_Match": 92.4,
            "Career_Velocity": 96.0,
            "Skill_Recency": 95.0,
            "Confidence_Interval": "97.2%",
            "Key_Strength_Summary": "Ranked #1 due to exceptional segment match in Distributed Training. Highly accelerated career velocity (2 promotions in 3 years at top tier firm). Active and recent deployment of PyTorch pipelines."
        },
        {
            "Rank": 2,
            "Candidate_ID": "CAND_109",
            "Semantic_Match": 89.5,
            "Career_Velocity": 85.0,
            "Skill_Recency": 90.0,
            "Confidence_Interval": "91.5%",
            "Key_Strength_Summary": "Strong core alignment. Layer 3 Skill Adjacency logic successfully bridged their deep TensorFlow/NumPy architecture background with your JD's PyTorch requirement, preventing keyword omission."
        },
        {
            "Rank": 3,
            "Candidate_ID": "CAND_077",
            "Semantic_Match": 81.0,
            "Career_Velocity": 92.5,
            "Skill_Recency": 88.0,
            "Confidence_Interval": "89.1%",
            "Key_Strength_Summary": "High potential profile. Career velocity is in the top 5% with continuous progression into Tech Lead roles. Minor score deficit in sub-millisecond serving, but offset by systems engineering depth."
        },
        {
            "Rank": 4,
            "Candidate_ID": "CAND_015",
            "Semantic_Match": 88.0,
            "Career_Velocity": 68.0,
            "Skill_Recency": 94.0,
            "Confidence_Interval": "84.3%",
            "Key_Strength_Summary": "Excellent technical currency. Deep hands-on recency with Kubeflow and Kubernetes. Overall rank adjusted due to multi-year static tenure at current employer (Moderate Career Velocity)."
        }
    ]
    
    for cand in candidates:
        raw_score = (cand["Semantic_Match"] * w_semantic) + (cand["Career_Velocity"] * w_velocity) + (cand["Skill_Recency"] * w_recency)
        cand["Overall_Score"] = round(raw_score, 1)
        
    candidates = sorted(candidates, key=lambda x: x["Overall_Score"], reverse=True)
    for i, cand in enumerate(candidates):
        cand["Rank"] = i + 1
        
    return pd.DataFrame(candidates)

st.markdown("---")

# Execution Button
if st.button("🔍 Run Intelligent Discovery Engine", type="primary"):
    if not jd_input.strip():
        st.error("Please enter a Job Description first to begin the discovery process.")
    else:
        with st.spinner("Processing... [Layer 1-4 Inbound Pipeline Active]"):
            time.sleep(1.8)
            df_results = generate_mock_shortlist(jd_input)
            st.markdown("### 🏆 Expertly Ranked Shortlist (Top Fit Candidates)")
            st.balloons()
            
            display_cols = ["Rank", "Candidate_ID", "Overall_Score", "Confidence_Interval", "Key_Strength_Summary"]
            st.dataframe(df_results[display_cols].set_index("Rank"), use_container_width=True)
            
            st.markdown("#### 📈 Discovery Insights")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Highest Candidate Score", f"{df_results['Overall_Score'].max()}%")
            m_col2.metric("Average Confidence Interval", "90.5%")
            m_col3.metric("Keyword Blindspots Bypassed", "4 Instances")
            
            st.markdown("#### 💾 Export Submission Data")
            csv_data = df_results[display_cols].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Ranked Candidates (CSV/XLSX format)",
                data=csv_data,
                file_name="ranked_candidates.csv",
                mime="text/csv"
            )
