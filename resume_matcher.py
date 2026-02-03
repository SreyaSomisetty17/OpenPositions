#!/usr/bin/env python3
"""
Resume Matcher Web App
Upload your resume to see match percentages for SWE internship positions.
"""

import streamlit as st
import json
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# PDF and DOCX parsing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


# Technical skills database for matching
TECH_SKILLS = {
    "languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
        "rust", "swift", "kotlin", "scala", "ruby", "php", "r", "matlab", "sql",
        "html", "css", "bash", "shell", "perl", "haskell", "elixir", "dart"
    ],
    "frameworks": [
        "react", "reactjs", "react.js", "angular", "vue", "vuejs", "vue.js",
        "node", "nodejs", "node.js", "express", "django", "flask", "fastapi",
        "spring", "spring boot", "springboot", ".net", "dotnet", "rails",
        "ruby on rails", "next.js", "nextjs", "nuxt", "svelte", "flutter"
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
        "dynamodb", "cassandra", "sqlite", "oracle", "sql server", "firebase",
        "neo4j", "graphql", "supabase"
    ],
    "cloud": [
        "aws", "amazon web services", "azure", "gcp", "google cloud", "heroku",
        "digitalocean", "vercel", "netlify", "cloudflare", "terraform",
        "kubernetes", "k8s", "docker", "containerization", "microservices"
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "jenkins",
        "ci/cd", "cicd", "linux", "unix", "agile", "scrum", "rest", "restful",
        "api", "graphql", "webpack", "npm", "yarn", "maven", "gradle"
    ],
    "ml_ai": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "sklearn", "pandas", "numpy", "opencv", "nlp",
        "natural language processing", "computer vision", "neural network",
        "llm", "large language model", "transformer", "bert", "gpt"
    ],
    "concepts": [
        "data structures", "algorithms", "oop", "object oriented", "design patterns",
        "system design", "distributed systems", "multithreading", "concurrency",
        "testing", "unit testing", "integration testing", "tdd", "debugging"
    ]
}


def extract_text_from_pdf(file) -> str:
    """Extract text from uploaded PDF file."""
    if not PDF_AVAILABLE:
        st.error("PyPDF2 not installed. Please install with: pip install PyPDF2")
        return ""
    
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""


def extract_text_from_docx(file) -> str:
    """Extract text from uploaded DOCX file."""
    if not DOCX_AVAILABLE:
        st.error("python-docx not installed. Please install with: pip install python-docx")
        return ""
    
    try:
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""


def extract_skills(text: str) -> dict:
    """Extract technical skills from text."""
    text_lower = text.lower()
    found_skills = {}
    
    for category, skills in TECH_SKILLS.items():
        found = []
        for skill in skills:
            # Use word boundaries for accurate matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.append(skill)
        if found:
            found_skills[category] = found
    
    return found_skills


def calculate_match_score(resume_text: str, job_title: str, job_location: str, job_description: str = "") -> tuple:
    """Calculate match score between resume and job."""
    
    # Create job description from title, location, and description
    job_text = f"{job_title} {job_location} {job_description}"
    
    # Extract skills from both
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    
    # Flatten skills
    resume_skills_flat = set()
    for skills in resume_skills.values():
        resume_skills_flat.update(skills)
    
    job_skills_flat = set()
    for skills in job_skills.values():
        job_skills_flat.update(skills)
    
    # TF-IDF similarity
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        similarity = 0
    
    # Skill overlap bonus
    if job_skills_flat:
        skill_match = len(resume_skills_flat & job_skills_flat) / len(job_skills_flat)
    else:
        skill_match = 0.5  # Neutral if job has no detected skills
    
    # Combined score (weighted)
    # 40% TF-IDF similarity + 60% skill match
    combined_score = (0.4 * similarity + 0.6 * skill_match) * 100
    
    # Boost for intern/internship keywords in resume
    intern_keywords = ["intern", "internship", "co-op", "student", "university", "bachelor", "master", "gpa"]
    intern_matches = sum(1 for kw in intern_keywords if kw in resume_text.lower())
    intern_boost = min(intern_matches * 2, 10)  # Max 10% boost
    
    final_score = min(combined_score + intern_boost, 100)
    
    # Missing skills
    missing_skills = job_skills_flat - resume_skills_flat
    
    return round(final_score, 1), list(missing_skills), list(resume_skills_flat)


def load_jobs() -> list:
    """Load jobs from jobs.json file."""
    jobs_file = Path("jobs.json")
    if not jobs_file.exists():
        return []
    
    try:
        with open(jobs_file, "r") as f:
            data = json.load(f)
            # Handle both dict format (with "faang"/"other" keys) and list format
            if isinstance(data, dict):
                jobs = []
                for category, job_list in data.items():
                    for job in job_list:
                        job["category"] = category.upper() if category == "faang" else category.title()
                        jobs.append(job)
                return jobs
            return data
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        return []


def main():
    st.set_page_config(
        page_title="SWE Internship Resume Matcher",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 SWE Internship Resume Matcher")
    st.markdown("Upload your resume to see how well you match with current Software Engineering internship openings!")
    
    # Sidebar for resume upload
    with st.sidebar:
        st.header("📄 Upload Your Resume")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT"
        )
        
        resume_text = ""
        
        if uploaded_file:
            file_type = uploaded_file.name.split(".")[-1].lower()
            
            if file_type == "pdf":
                resume_text = extract_text_from_pdf(uploaded_file)
            elif file_type == "docx":
                resume_text = extract_text_from_docx(uploaded_file)
            elif file_type == "txt":
                resume_text = uploaded_file.read().decode("utf-8")
            
            if resume_text:
                st.success(f"✅ Resume loaded! ({len(resume_text.split())} words)")
                
                # Show extracted skills
                st.subheader("🔍 Detected Skills")
                skills = extract_skills(resume_text)
                
                for category, skill_list in skills.items():
                    st.markdown(f"**{category.replace('_', ' ').title()}**")
                    st.markdown(", ".join([f"`{s}`" for s in skill_list]))
        
        st.markdown("---")
        st.markdown("### 📊 Filters")
        
        min_match = st.slider("Minimum Match %", 0, 100, 0, 5)
        
        category_filter = st.selectbox(
            "Category",
            ["All", "FAANG+", "FAANG", "Other"]
        )
    
    # Main content
    jobs = load_jobs()
    
    if not jobs:
        st.warning("⚠️ No jobs found. Please run `python scraper.py` first to fetch job listings.")
        st.code("python scraper.py", language="bash")
        return
    
    if not resume_text:
        st.info("👈 Upload your resume in the sidebar to see match percentages!")
        
        # Still show jobs without match scores
        st.subheader(f"📋 Current Openings ({len(jobs)} positions)")
        
        job_data = []
        for job in jobs:
            job_data.append({
                "Company": job.get("company", "Unknown"),
                "Role": job.get("title", "Unknown"),
                "Location": job.get("location", "Unknown"),
                "Category": job.get("category", "Other")
            })
        
        df = pd.DataFrame(job_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        return
    
    # Calculate match scores
    st.subheader("🎯 Job Matches")
    
    results = []
    
    progress_bar = st.progress(0)
    for i, job in enumerate(jobs):
        score, missing, _ = calculate_match_score(
            resume_text,
            job.get("title", ""),
            job.get("location", ""),
            job.get("description", "")
        )
        
        results.append({
            "company": job.get("company", "Unknown"),
            "title": job.get("title", "Unknown"),
            "location": job.get("location", "Unknown"),
            "category": job.get("category", "Other"),
            "match": score,
            "missing_skills": missing,
            "apply_url": job.get("url", job.get("apply_url", "#"))
        })
        
        progress_bar.progress((i + 1) / len(jobs))
    
    progress_bar.empty()
    
    # Sort by match score
    results.sort(key=lambda x: x["match"], reverse=True)
    
    # Apply filters
    if min_match > 0:
        results = [r for r in results if r["match"] >= min_match]
    
    if category_filter != "All":
        cat_lower = category_filter.lower().replace("+", "")
        results = [r for r in results if cat_lower in r["category"].lower()]
    
    if not results:
        st.warning("No jobs match your criteria. Try adjusting the filters.")
        return
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Matches", len(results))
    
    with col2:
        avg_score = sum(r["match"] for r in results) / len(results)
        st.metric("Average Match", f"{avg_score:.1f}%")
    
    with col3:
        high_matches = len([r for r in results if r["match"] >= 70])
        st.metric("High Matches (≥70%)", high_matches)
    
    with col4:
        top_match = results[0]["match"] if results else 0
        st.metric("Top Match", f"{top_match}%")
    
    st.markdown("---")
    
    # Display results
    for i, result in enumerate(results):
        match_color = "🟢" if result["match"] >= 70 else "🟡" if result["match"] >= 50 else "🔴"
        
        with st.expander(
            f"{match_color} **{result['match']}%** | {result['company']} - {result['title']}",
            expanded=(i < 5)  # Auto-expand top 5
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Company:** {result['company']}")
                st.markdown(f"**Role:** {result['title']}")
                st.markdown(f"**Location:** {result['location']}")
                st.markdown(f"**Category:** {result['category']}")
                
                if result["missing_skills"]:
                    st.markdown("**Skills to Add:**")
                    st.markdown(", ".join([f"`{s}`" for s in result["missing_skills"][:5]]))
            
            with col2:
                if result["apply_url"] and result["apply_url"] != "#":
                    st.link_button("🔗 Apply Now", result["apply_url"], use_container_width=True)
    
    # Export option
    st.markdown("---")
    
    df_export = pd.DataFrame([
        {
            "Company": r["company"],
            "Role": r["title"],
            "Location": r["location"],
            "Match %": r["match"],
            "Category": r["category"],
            "Apply URL": r["apply_url"]
        }
        for r in results
    ])
    
    csv = df_export.to_csv(index=False)
    st.download_button(
        "📥 Download Results as CSV",
        csv,
        "job_matches.csv",
        "text/csv",
        use_container_width=True
    )


if __name__ == "__main__":
    main()
