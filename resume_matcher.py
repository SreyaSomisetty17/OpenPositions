#!/usr/bin/env python3
"""
Advanced Resume Matcher Web App
Uses intelligent semantic matching for real-world job compatibility scoring.
"""

import streamlit as st
import json
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from collections import defaultdict

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


# ============================================================================
# COMPREHENSIVE SKILL TAXONOMY WITH RELATIONSHIPS
# ============================================================================

SKILL_CATEGORIES = {
    "programming_languages": {
        "python": ["python", "python3", "py"],
        "java": ["java", "jvm"],
        "javascript": ["javascript", "js", "ecmascript", "es6", "es2015"],
        "typescript": ["typescript", "ts"],
        "cpp": ["c++", "cpp", "c plus plus"],
        "c": ["c programming", " c ", "c language"],
        "csharp": ["c#", "csharp", "c sharp"],
        "go": ["go", "golang"],
        "rust": ["rust", "rustlang"],
        "swift": ["swift"],
        "kotlin": ["kotlin"],
        "scala": ["scala"],
        "ruby": ["ruby"],
        "php": ["php"],
        "r": [" r ", "r programming", "rstats"],
        "matlab": ["matlab"],
        "sql": ["sql", "mysql", "postgresql", "sqlite"],
        "html": ["html", "html5"],
        "css": ["css", "css3", "sass", "scss", "less"],
        "bash": ["bash", "shell", "zsh", "scripting"],
    },
    "frameworks_libraries": {
        "react": ["react", "reactjs", "react.js", "react native"],
        "angular": ["angular", "angularjs"],
        "vue": ["vue", "vuejs", "vue.js", "nuxt"],
        "nextjs": ["next.js", "nextjs", "next"],
        "nodejs": ["node", "nodejs", "node.js"],
        "express": ["express", "expressjs"],
        "django": ["django"],
        "flask": ["flask"],
        "fastapi": ["fastapi", "fast api"],
        "spring": ["spring", "spring boot", "springboot"],
        "dotnet": [".net", "dotnet", "asp.net"],
        "rails": ["rails", "ruby on rails", "ror"],
        "svelte": ["svelte", "sveltekit"],
        "flutter": ["flutter"],
        "pytorch": ["pytorch", "torch"],
        "tensorflow": ["tensorflow", "tf"],
        "keras": ["keras"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "scikit": ["scikit-learn", "sklearn", "scikit"],
    },
    "databases": {
        "mysql": ["mysql"],
        "postgresql": ["postgresql", "postgres", "psql"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "elasticsearch": ["elasticsearch", "elastic"],
        "dynamodb": ["dynamodb", "dynamo"],
        "cassandra": ["cassandra"],
        "sqlite": ["sqlite"],
        "oracle": ["oracle", "oracle db"],
        "firebase": ["firebase", "firestore"],
        "neo4j": ["neo4j", "graph database"],
        "supabase": ["supabase"],
    },
    "cloud_devops": {
        "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudfront"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "docker": ["docker", "containerization", "containers"],
        "kubernetes": ["kubernetes", "k8s", "kubectl"],
        "terraform": ["terraform", "iac", "infrastructure as code"],
        "jenkins": ["jenkins"],
        "cicd": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
        "github_actions": ["github actions"],
        "gitlab_ci": ["gitlab ci", "gitlab-ci"],
        "ansible": ["ansible"],
        "linux": ["linux", "unix", "ubuntu", "centos", "debian"],
    },
    "concepts": {
        "data_structures": ["data structures", "arrays", "linked list", "trees", "graphs", "heap", "stack", "queue"],
        "algorithms": ["algorithms", "sorting", "searching", "dynamic programming", "recursion", "big o"],
        "system_design": ["system design", "distributed systems", "scalability", "microservices"],
        "oop": ["oop", "object oriented", "object-oriented", "inheritance", "polymorphism"],
        "api_design": ["api", "rest", "restful", "graphql", "grpc"],
        "testing": ["testing", "unit test", "integration test", "tdd", "jest", "pytest", "junit"],
        "agile": ["agile", "scrum", "kanban", "sprint"],
        "version_control": ["git", "github", "gitlab", "bitbucket", "version control"],
    },
    "ml_ai": {
        "machine_learning": ["machine learning", "ml", "supervised learning", "unsupervised learning"],
        "deep_learning": ["deep learning", "neural network", "cnn", "rnn", "lstm", "transformer"],
        "nlp": ["nlp", "natural language processing", "text processing", "language model"],
        "computer_vision": ["computer vision", "image processing", "opencv", "object detection"],
        "llm": ["llm", "large language model", "gpt", "bert", "chatgpt", "langchain"],
        "data_science": ["data science", "data analysis", "visualization", "statistics"],
    },
    "soft_skills": {
        "leadership": ["leadership", "led", "managed", "mentored", "coordinated"],
        "communication": ["communication", "presented", "collaborated", "teamwork"],
        "problem_solving": ["problem solving", "analytical", "critical thinking", "debugging"],
    }
}

# Skill relationships for semantic matching (related skills boost score)
SKILL_RELATIONSHIPS = {
    "python": ["django", "flask", "fastapi", "pandas", "numpy", "pytorch", "tensorflow"],
    "javascript": ["react", "angular", "vue", "nodejs", "express", "nextjs", "typescript"],
    "typescript": ["react", "angular", "nodejs", "nextjs"],
    "java": ["spring", "kotlin", "android"],
    "react": ["javascript", "typescript", "nextjs", "redux"],
    "nodejs": ["javascript", "express", "typescript"],
    "aws": ["docker", "kubernetes", "terraform", "cicd"],
    "docker": ["kubernetes", "aws", "gcp", "azure", "cicd"],
    "machine_learning": ["python", "pytorch", "tensorflow", "pandas", "numpy"],
    "data_science": ["python", "sql", "pandas", "numpy", "statistics"],
}

# Education level weights
EDUCATION_LEVELS = {
    "phd": 1.0,
    "ph.d": 1.0,
    "doctorate": 1.0,
    "master": 0.9,
    "masters": 0.9,
    "m.s.": 0.9,
    "m.s": 0.9,
    "mba": 0.85,
    "bachelor": 0.8,
    "bachelors": 0.8,
    "b.s.": 0.8,
    "b.s": 0.8,
    "b.a.": 0.75,
    "undergraduate": 0.7,
    "pursuing": 0.65,
    "student": 0.6,
}

# Relevant majors for SWE
RELEVANT_MAJORS = [
    "computer science", "cs", "software engineering", "computer engineering",
    "electrical engineering", "information technology", "data science",
    "mathematics", "math", "physics", "statistics", "applied mathematics",
    "information systems", "computational", "artificial intelligence"
]

# Top tech companies for experience bonus
TOP_COMPANIES = [
    "google", "meta", "facebook", "amazon", "apple", "microsoft", "netflix",
    "stripe", "airbnb", "uber", "lyft", "doordash", "coinbase", "robinhood",
    "databricks", "snowflake", "figma", "notion", "discord", "slack",
    "twitter", "linkedin", "salesforce", "adobe", "nvidia", "intel", "amd",
    "openai", "anthropic", "deepmind", "palantir", "snap", "pinterest",
    "spotify", "dropbox", "oracle", "ibm", "cisco", "vmware", "intuit"
]


# ============================================================================
# TEXT EXTRACTION FUNCTIONS
# ============================================================================

def extract_text_from_pdf(file) -> str:
    """Extract text from uploaded PDF file."""
    if not PDF_AVAILABLE:
        st.error("PyPDF2 not installed.")
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
        st.error("python-docx not installed.")
        return ""
    try:
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""


# ============================================================================
# INTELLIGENT RESUME ANALYSIS
# ============================================================================

def extract_skills_advanced(text: str) -> tuple:
    """Extract skills with category information."""
    text_lower = text.lower()
    found_skills = defaultdict(list)
    all_skills = set()
    
    for category, skill_dict in SKILL_CATEGORIES.items():
        for skill_name, variations in skill_dict.items():
            for variation in variations:
                # Use word boundaries for accurate matching
                pattern = r'\b' + re.escape(variation) + r'\b'
                if re.search(pattern, text_lower):
                    if skill_name not in found_skills[category]:
                        found_skills[category].append(skill_name)
                        all_skills.add(skill_name)
                    break  # Found this skill, move to next
    
    return dict(found_skills), all_skills


def extract_education(text: str) -> dict:
    """Extract education information from resume."""
    text_lower = text.lower()
    
    education = {
        "level": 0.5,  # Default baseline
        "level_name": "Unknown",
        "relevant_major": False,
        "gpa": None,
        "university_tier": "standard"
    }
    
    # Find highest education level
    for level, weight in EDUCATION_LEVELS.items():
        if level in text_lower:
            if weight > education["level"]:
                education["level"] = weight
                education["level_name"] = level.title()
    
    # Check for relevant major
    for major in RELEVANT_MAJORS:
        if major in text_lower:
            education["relevant_major"] = True
            break
    
    # Extract GPA (look for patterns like 3.8, 3.85/4.0, GPA: 3.9)
    gpa_patterns = [
        r'gpa[:\s]*([0-3]\.[0-9]{1,2})',
        r'([0-3]\.[0-9]{1,2})[/\s]*4\.0',
        r'([0-3]\.[0-9]{1,2})[/\s]*gpa',
    ]
    for pattern in gpa_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                gpa = float(match.group(1))
                if 2.0 <= gpa <= 4.0:
                    education["gpa"] = gpa
                    break
            except:
                pass
    
    # Check for top universities (simplified list)
    top_universities = [
        "stanford", "mit", "berkeley", "carnegie mellon", "cmu",
        "harvard", "princeton", "yale", "columbia", "cornell",
        "caltech", "georgia tech", "university of washington",
        "ucla", "usc", "university of michigan", "illinois",
        "purdue", "university of texas", "ut austin"
    ]
    for uni in top_universities:
        if uni in text_lower:
            education["university_tier"] = "top"
            break
    
    return education


def extract_experience(text: str) -> dict:
    """Extract work/project experience from resume."""
    text_lower = text.lower()
    
    experience = {
        "has_internship": False,
        "has_top_company": False,
        "top_companies": [],
        "project_count": 0,
        "has_research": False,
        "years_experience": 0
    }
    
    # Check for internship experience
    internship_patterns = ["intern", "internship", "co-op", "coop"]
    for pattern in internship_patterns:
        if pattern in text_lower:
            experience["has_internship"] = True
            break
    
    # Check for top company experience
    for company in TOP_COMPANIES:
        if company in text_lower:
            experience["has_top_company"] = True
            experience["top_companies"].append(company.title())
    
    # Count projects (look for "project" mentions)
    project_matches = re.findall(r'\bproject\b', text_lower)
    experience["project_count"] = min(len(project_matches), 10)  # Cap at 10
    
    # Check for research experience
    research_patterns = ["research", "publication", "paper", "thesis", "dissertation"]
    for pattern in research_patterns:
        if pattern in text_lower:
            experience["has_research"] = True
            break
    
    # Try to estimate years of experience
    year_patterns = [
        r'(\d+)\+?\s*years?\s*(of\s*)?(experience|work)',
        r'(experience|worked)\s*(\d+)\+?\s*years?',
    ]
    for pattern in year_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                years = int(match.group(1)) if match.group(1).isdigit() else int(match.group(2))
                experience["years_experience"] = min(years, 10)
                break
            except:
                pass
    
    return experience


def analyze_resume(text: str) -> dict:
    """Comprehensive resume analysis."""
    skills_by_category, all_skills = extract_skills_advanced(text)
    education = extract_education(text)
    experience = extract_experience(text)
    
    return {
        "skills_by_category": skills_by_category,
        "all_skills": all_skills,
        "education": education,
        "experience": experience,
        "word_count": len(text.split()),
        "raw_text": text
    }


# ============================================================================
# INTELLIGENT JOB MATCHING
# ============================================================================

def calculate_skill_match(resume_skills: set, job_title: str, job_description: str) -> tuple:
    """Calculate skill match with semantic understanding."""
    job_text = f"{job_title} {job_description}".lower()
    
    # Extract skills from job
    job_skills_by_cat, job_skills = extract_skills_advanced(job_text)
    
    if not job_skills:
        # If no specific skills in job, use general SWE requirements
        job_skills = {"python", "java", "javascript", "data_structures", "algorithms", "version_control"}
    
    # Direct skill matches
    direct_matches = resume_skills & job_skills
    
    # Related skill matches (partial credit)
    related_matches = set()
    for skill in resume_skills:
        if skill in SKILL_RELATIONSHIPS:
            for related in SKILL_RELATIONSHIPS[skill]:
                if related in job_skills and related not in direct_matches:
                    related_matches.add(related)
    
    # Calculate score
    total_job_skills = len(job_skills)
    direct_score = len(direct_matches) / total_job_skills if total_job_skills > 0 else 0
    related_score = (len(related_matches) * 0.5) / total_job_skills if total_job_skills > 0 else 0
    
    skill_score = min(direct_score + related_score, 1.0)
    
    # Bonus for having many relevant skills
    if len(resume_skills) >= 15:
        skill_score = min(skill_score + 0.15, 1.0)
    elif len(resume_skills) >= 10:
        skill_score = min(skill_score + 0.1, 1.0)
    elif len(resume_skills) >= 5:
        skill_score = min(skill_score + 0.05, 1.0)
    
    # Missing skills (for recommendations)
    missing = job_skills - resume_skills - related_matches
    
    return skill_score, list(direct_matches), list(missing)


def calculate_education_match(education: dict, job_title: str) -> float:
    """Calculate education match score."""
    score = education["level"]  # Base from education level
    
    # Bonus for relevant major
    if education["relevant_major"]:
        score += 0.1
    
    # GPA bonus (if high)
    if education["gpa"]:
        if education["gpa"] >= 3.7:
            score += 0.1
        elif education["gpa"] >= 3.5:
            score += 0.05
    
    # University tier bonus
    if education["university_tier"] == "top":
        score += 0.05
    
    return min(score, 1.0)


def calculate_experience_match(experience: dict, job_title: str, company: str) -> float:
    """Calculate experience match score."""
    score = 0.5  # Baseline
    
    # Internship experience is highly valuable for intern roles
    if experience["has_internship"]:
        score += 0.2
    
    # Top company experience is valuable
    if experience["has_top_company"]:
        score += 0.15
        # Extra bonus if same/similar company
        company_lower = company.lower()
        for top_co in experience["top_companies"]:
            if top_co.lower() in company_lower or company_lower in top_co.lower():
                score += 0.1
                break
    
    # Projects are valuable
    if experience["project_count"] >= 3:
        score += 0.1
    elif experience["project_count"] >= 1:
        score += 0.05
    
    # Research experience bonus for certain roles
    if experience["has_research"]:
        if any(kw in job_title.lower() for kw in ["research", "ml", "machine learning", "ai", "data"]):
            score += 0.1
    
    return min(score, 1.0)


def calculate_text_similarity(resume_text: str, job_title: str, job_description: str) -> float:
    """Calculate semantic text similarity using TF-IDF."""
    job_text = f"{job_title} {job_description}"
    
    if len(job_text.strip()) < 10:
        # If job description is too short, use title-based matching
        job_text = f"{job_title} software engineer intern programming development coding"
    
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity
    except:
        return 0.3  # Default moderate similarity


def calculate_match_score(resume_analysis: dict, job: dict) -> dict:
    """
    Calculate comprehensive match score between resume and job.
    
    Scoring breakdown:
    - Skills: 40%
    - Experience: 25%
    - Education: 15%
    - Text Similarity: 15%
    - Bonus factors: 5%
    """
    job_title = job.get("title", "")
    job_description = job.get("description", "")
    company = job.get("company", "")
    
    # Calculate component scores
    skill_score, matched_skills, missing_skills = calculate_skill_match(
        resume_analysis["all_skills"],
        job_title,
        job_description
    )
    
    education_score = calculate_education_match(
        resume_analysis["education"],
        job_title
    )
    
    experience_score = calculate_experience_match(
        resume_analysis["experience"],
        job_title,
        company
    )
    
    text_similarity = calculate_text_similarity(
        resume_analysis["raw_text"],
        job_title,
        job_description
    )
    
    # Bonus factors
    bonus = 0
    
    # Bonus for having many skills
    if len(resume_analysis["all_skills"]) >= 10:
        bonus += 0.03
    
    # Bonus for comprehensive resume
    if resume_analysis["word_count"] >= 300:
        bonus += 0.02
    
    # Calculate weighted final score
    final_score = (
        skill_score * 0.40 +
        experience_score * 0.25 +
        education_score * 0.15 +
        text_similarity * 0.15 +
        bonus
    ) * 100
    
    # Apply floor and ceiling
    final_score = max(25, min(98, final_score))  # Range: 25-98%
    
    # Determine match quality
    if final_score >= 75:
        match_quality = "Excellent"
    elif final_score >= 60:
        match_quality = "Good"
    elif final_score >= 45:
        match_quality = "Fair"
    else:
        match_quality = "Needs Work"
    
    return {
        "score": round(final_score, 1),
        "quality": match_quality,
        "breakdown": {
            "skills": round(skill_score * 100, 1),
            "experience": round(experience_score * 100, 1),
            "education": round(education_score * 100, 1),
            "relevance": round(text_similarity * 100, 1)
        },
        "matched_skills": matched_skills[:10],
        "missing_skills": missing_skills[:5],
        "recommendations": generate_recommendations(resume_analysis, missing_skills)
    }


def generate_recommendations(resume_analysis: dict, missing_skills: list) -> list:
    """Generate personalized recommendations."""
    recommendations = []
    
    # Skill recommendations
    if missing_skills:
        skill_str = ", ".join(missing_skills[:3])
        recommendations.append(f"Consider adding: {skill_str}")
    
    # Experience recommendations
    exp = resume_analysis["experience"]
    if not exp["has_internship"]:
        recommendations.append("Prior internship experience would strengthen your application")
    if exp["project_count"] < 2:
        recommendations.append("Add more personal/academic projects to showcase skills")
    
    # Education recommendations
    edu = resume_analysis["education"]
    if edu["gpa"] and edu["gpa"] < 3.5:
        recommendations.append("Highlight relevant coursework and projects over GPA")
    
    return recommendations[:3]  # Top 3 recommendations


# ============================================================================
# DATA LOADING
# ============================================================================

def load_jobs() -> list:
    """Load jobs from jobs.json file."""
    jobs_file = Path("jobs.json")
    if not jobs_file.exists():
        return []
    
    try:
        with open(jobs_file, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                jobs = []
                for category, job_list in data.items():
                    for job in job_list:
                        job["category"] = "FAANG+" if category.lower() == "faang" else category.title()
                        jobs.append(job)
                return jobs
            return data
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        return []


# ============================================================================
# STREAMLIT APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="AI Resume Matcher",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 AI-Powered Resume Matcher")
    st.markdown("""
    Upload your resume to see how well you match with SWE internship positions.
    Our AI analyzes your **skills, education, experience**, and more!
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("📄 Upload Resume")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt"],
            help="Supported: PDF, DOCX, TXT"
        )
        
        resume_text = ""
        resume_analysis = None
        
        if uploaded_file:
            file_type = uploaded_file.name.split(".")[-1].lower()
            
            if file_type == "pdf":
                resume_text = extract_text_from_pdf(uploaded_file)
            elif file_type == "docx":
                resume_text = extract_text_from_docx(uploaded_file)
            elif file_type == "txt":
                resume_text = uploaded_file.read().decode("utf-8")
            
            if resume_text:
                resume_analysis = analyze_resume(resume_text)
                st.success(f"✅ Resume analyzed! ({resume_analysis['word_count']} words)")
                
                # Show analysis summary
                st.markdown("---")
                st.subheader("📊 Resume Analysis")
                
                # Skills
                st.markdown("**🔧 Skills Detected:**")
                skills = resume_analysis["skills_by_category"]
                for category, skill_list in skills.items():
                    cat_name = category.replace("_", " ").title()
                    st.markdown(f"*{cat_name}:* {', '.join(skill_list)}")
                
                # Education
                st.markdown("---")
                st.markdown("**🎓 Education:**")
                edu = resume_analysis["education"]
                st.markdown(f"Level: {edu['level_name']}")
                if edu["gpa"]:
                    st.markdown(f"GPA: {edu['gpa']}")
                if edu["relevant_major"]:
                    st.markdown("✅ Relevant CS/Tech major")
                
                # Experience
                st.markdown("---")
                st.markdown("**💼 Experience:**")
                exp = resume_analysis["experience"]
                if exp["has_internship"]:
                    st.markdown("✅ Has internship experience")
                if exp["has_top_company"]:
                    st.markdown(f"✅ Worked at: {', '.join(exp['top_companies'][:3])}")
                st.markdown(f"Projects mentioned: {exp['project_count']}")
        
        st.markdown("---")
        st.subheader("📊 Filters")
        
        min_match = st.slider("Minimum Match %", 0, 100, 0, 5)
        
        category_filter = st.selectbox("Category", ["All", "FAANG+", "Other"])
    
    # Main content
    jobs = load_jobs()
    
    if not jobs:
        st.warning("⚠️ No jobs found. Run `python scraper.py` first.")
        return
    
    if not resume_analysis:
        st.info("👈 Upload your resume in the sidebar to see personalized match scores!")
        
        st.subheader(f"📋 Available Positions ({len(jobs)})")
        df = pd.DataFrame([{
            "Company": j.get("company", "Unknown"),
            "Role": j.get("title", "Unknown"),
            "Location": j.get("location", "Unknown"),
            "Category": j.get("category", "Other")
        } for j in jobs])
        st.dataframe(df, use_container_width=True, hide_index=True)
        return
    
    # Calculate matches
    st.subheader("🎯 Your Job Matches")
    
    results = []
    progress = st.progress(0)
    
    for i, job in enumerate(jobs):
        match_result = calculate_match_score(resume_analysis, job)
        
        results.append({
            "company": job.get("company", "Unknown"),
            "title": job.get("title", "Unknown"),
            "location": job.get("location", "Unknown"),
            "category": job.get("category", "Other"),
            "score": match_result["score"],
            "quality": match_result["quality"],
            "breakdown": match_result["breakdown"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "recommendations": match_result["recommendations"],
            "url": job.get("url", job.get("apply_url", "#"))
        })
        progress.progress((i + 1) / len(jobs))
    
    progress.empty()
    
    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Apply filters
    if min_match > 0:
        results = [r for r in results if r["score"] >= min_match]
    
    if category_filter != "All":
        results = [r for r in results if category_filter.lower().replace("+", "") in r["category"].lower()]
    
    if not results:
        st.warning("No jobs match your criteria.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Matches", len(results))
    with col2:
        avg = sum(r["score"] for r in results) / len(results)
        st.metric("Average Match", f"{avg:.1f}%")
    with col3:
        excellent = len([r for r in results if r["score"] >= 70])
        st.metric("Excellent Matches", excellent)
    with col4:
        st.metric("Best Match", f"{results[0]['score']}%")
    
    st.markdown("---")
    
    # Display results
    for i, r in enumerate(results):
        icon = "🟢" if r["score"] >= 70 else "🟡" if r["score"] >= 50 else "🔴"
        
        with st.expander(
            f"{icon} **{r['score']}%** ({r['quality']}) | {r['company']} - {r['title']}",
            expanded=(i < 3)
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Company:** {r['company']}")
                st.markdown(f"**Role:** {r['title']}")
                st.markdown(f"**Location:** {r['location']}")
                
                # Score breakdown
                st.markdown("**Score Breakdown:**")
                breakdown = r["breakdown"]
                cols = st.columns(4)
                cols[0].metric("Skills", f"{breakdown['skills']}%")
                cols[1].metric("Experience", f"{breakdown['experience']}%")
                cols[2].metric("Education", f"{breakdown['education']}%")
                cols[3].metric("Relevance", f"{breakdown['relevance']}%")
                
                # Matched skills
                if r["matched_skills"]:
                    st.markdown(f"**✅ Matching Skills:** {', '.join(r['matched_skills'])}")
                
                # Missing skills
                if r["missing_skills"]:
                    st.markdown(f"**📝 Consider Adding:** {', '.join(r['missing_skills'])}")
                
                # Recommendations
                if r["recommendations"]:
                    st.markdown("**💡 Tips:**")
                    for rec in r["recommendations"]:
                        st.markdown(f"- {rec}")
            
            with col2:
                if r["url"] and r["url"] != "#":
                    st.link_button("🔗 Apply Now", r["url"], use_container_width=True)
    
    # Export
    st.markdown("---")
    df_export = pd.DataFrame([{
        "Company": r["company"],
        "Role": r["title"],
        "Location": r["location"],
        "Match %": r["score"],
        "Quality": r["quality"],
        "Category": r["category"]
    } for r in results])
    
    st.download_button(
        "📥 Download Results",
        df_export.to_csv(index=False),
        "job_matches.csv",
        "text/csv",
        use_container_width=True
    )


if __name__ == "__main__":
    main()
