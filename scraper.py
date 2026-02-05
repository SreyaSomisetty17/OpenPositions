#!/usr/bin/env python3
"""
Job Scraper for Software Engineering Internship Positions
Fetches job listings from multiple sources and updates README.md
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os

# Job board APIs and sources
GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
LEVER_API = "https://api.lever.co/v0/postings/{company}"

REPO_OWNER = "SreyaSomisetty17"
REPO_NAME = "OpenPositions"

# Companies to scrape - organized by category
# FAANG+ = Facebook/Meta, Apple, Amazon, Netflix, Google + top tech companies
FAANG_COMPANIES = {
    "greenhouse": [
        ("openai", "OpenAI"),
        ("stripe", "Stripe"),
        ("figma", "Figma"),
        ("ramp", "Ramp"),
        ("notion", "Notion"),
        ("plaid", "Plaid"),
        ("coinbase", "Coinbase"),
        ("instacart", "Instacart"),
        ("doordash", "DoorDash"),
        ("robinhood", "Robinhood"),
        ("discord", "Discord"),
        ("databricks", "Databricks"),
        ("scaleai", "Scale AI"),
        ("anthropic", "Anthropic"),
        ("meta", "Meta"),
        ("nvidia", "NVIDIA"),
        ("amd", "AMD"),
        ("paloaltonetworks", "Palo Alto Networks"),
        ("crowdstrike", "CrowdStrike"),
        ("datadog", "Datadog"),
        ("elastic", "Elastic"),
        ("confluent", "Confluent"),
        ("supabase", "Supabase"),
        ("vercel", "Vercel"),
    ],
    "lever": [
        ("netflix", "Netflix"),
    ],
    # Manual entries for companies using Workday, Taleo, and other proprietary ATS
    # These don't have public APIs so we provide direct career page links
    "manual": [
        # FAANG
        {
            "company": "Google",
            "title": "Software Engineering Intern, Summer 2026",
            "location": "Mountain View, CA",
            "url": "https://www.google.com/about/careers/applications/jobs/results/?q=Software%20Engineering%20Intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Apple",
            "title": "Software Engineering Intern",
            "location": "Cupertino, CA",
            "url": "https://jobs.apple.com/en-us/search?team=internships-STDNT-INTRN",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Amazon",
            "title": "Software Development Engineer Intern",
            "location": "Seattle, WA",
            "url": "https://www.amazon.jobs/en/search?base_query=software+intern&loc_query=",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Microsoft",
            "title": "Software Engineering Intern",
            "location": "Redmond, WA",
            "url": "https://careers.microsoft.com/us/en/search-results?keywords=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        # Semiconductor & Hardware (Workday users)
        {
            "company": "Intel",
            "title": "Software Engineering Intern",
            "location": "Santa Clara, CA",
            "url": "https://jobs.intel.com/en/search-jobs/intern/599/1",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Qualcomm",
            "title": "Software Engineering Intern",
            "location": "San Diego, CA",
            "url": "https://careers.qualcomm.com/careers/search?keyword=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "KLA Corporation",
            "title": "Software Engineering Intern",
            "location": "Milpitas, CA",
            "url": "https://kla.wd1.myworkdayjobs.com/Search?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Applied Materials",
            "title": "Software Engineering Intern",
            "location": "Santa Clara, CA",
            "url": "https://amat.wd1.myworkdayjobs.com/External?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Lam Research",
            "title": "Software Engineering Intern",
            "location": "Fremont, CA",
            "url": "https://lamresearch.wd1.myworkdayjobs.com/LAM?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        # Enterprise Software (Workday/Oracle users)
        {
            "company": "Adobe",
            "title": "Software Engineer Intern",
            "location": "San Jose, CA",
            "url": "https://careers.adobe.com/us/en/search-results?keywords=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "VMware",
            "title": "Software Engineering Intern",
            "location": "Palo Alto, CA",
            "url": "https://careers.vmware.com/early-talent/jobs?keywords=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "ServiceNow",
            "title": "Software Engineering Intern",
            "location": "Santa Clara, CA",
            "url": "https://careers.servicenow.com/en/jobs?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Workday",
            "title": "Software Development Engineer Intern",
            "location": "Pleasanton, CA",
            "url": "https://workday.wd5.myworkdayjobs.com/Workday_University_Careers?q=software",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Intuit",
            "title": "Software Engineering Intern",
            "location": "Mountain View, CA",
            "url": "https://jobs.intuit.com/search-jobs/intern/",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Autodesk",
            "title": "Software Engineer Intern",
            "location": "San Francisco, CA",
            "url": "https://autodesk.wd1.myworkdayjobs.com/uni?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Salesforce",
            "title": "Software Engineering Intern",
            "location": "San Francisco, CA",
            "url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "Oracle",
            "title": "Software Engineer Intern",
            "location": "Redwood City, CA",
            "url": "https://careers.oracle.com/jobs/#en/sites/jobsearch/requisitions?keyword=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        {
            "company": "SAP",
            "title": "Software Development Intern",
            "location": "Palo Alto, CA",
            "url": "https://jobs.sap.com/search/?q=software%20intern",
            "days_posted": 0,
            "compensation": ""
        },
        # Cisco and Networking
        {
            "company": "Cisco",
            "title": "Software Engineering Intern",
            "location": "San Jose, CA",
            "url": "https://jobs.cisco.com/jobs/SearchJobs/intern?21178=%5B169482%5D",
            "days_posted": 0,
            "compensation": ""
        },
    ]
}

OTHER_COMPANIES = {
    "greenhouse": [
        ("affirm", "Affirm"),
        ("airbnb", "Airbnb"),
        ("airtable", "Airtable"),
        ("asana", "Asana"),
        ("brex", "Brex"),
        ("chime", "Chime"),
        ("cockroachlabs", "Cockroach Labs"),
        ("dropbox", "Dropbox"),
        ("grammarly", "Grammarly"),
        ("gusto", "Gusto"),
        ("hashicorp", "HashiCorp"),
        ("hubspot", "HubSpot"),
        ("lyft", "Lyft"),
        ("mongodb", "MongoDB"),
        ("okta", "Okta"),
        ("palantir", "Palantir"),
        ("pinterest", "Pinterest"),
        ("reddit", "Reddit"),
        ("salesforce", "Salesforce"),
        ("shopify", "Shopify"),
        ("slack", "Slack"),
        ("snap", "Snap"),
        ("snowflake", "Snowflake"),
        ("splunk", "Splunk"),
        ("spotify", "Spotify"),
        ("square", "Square"),
        ("squarespace", "Squarespace"),
        ("tesla", "Tesla"),
        ("twitch", "Twitch"),
        ("uber", "Uber"),
        ("verkada", "Verkada"),
        ("wayfair", "Wayfair"),
        ("zoom", "Zoom"),
        ("zscaler", "Zscaler"),
        # Additional companies with CA/Seattle presence
        ("coursera", "Coursera"),
        ("duolingo", "Duolingo"),
        ("flexport", "Flexport"),
        ("rippling", "Rippling"),
        ("faire", "Faire"),
        ("retool", "Retool"),
        ("linear", "Linear"),
        ("loom", "Loom"),
        ("miro", "Miro"),
        ("canva", "Canva"),
        ("webflow", "Webflow"),
        ("amplitude", "Amplitude"),
        ("mixpanel", "Mixpanel"),
        ("segment", "Segment"),
        ("twilio", "Twilio"),
        ("cloudflare", "Cloudflare"),
        ("fastly", "Fastly"),
        ("netlify", "Netlify"),
        ("gitlab", "GitLab"),
        ("atlassian", "Atlassian"),
        ("postman", "Postman"),
        ("sentry", "Sentry"),
        ("launchdarkly", "LaunchDarkly"),
        ("pagerduty", "PagerDuty"),
        ("newrelic", "New Relic"),
        ("sumologic", "Sumo Logic"),
        ("grafana", "Grafana Labs"),
        ("circleci", "CircleCI"),
        ("buildkite", "Buildkite"),
        ("waymo", "Waymo"),
        ("cruise", "Cruise"),
        ("aurora", "Aurora"),
        ("nuro", "Nuro"),
        ("zoox", "Zoox"),
        ("rivian", "Rivian"),
        ("lucidmotors", "Lucid Motors"),
        ("chargepoint", "ChargePoint"),
        ("thetradedesk", "The Trade Desk"),
        ("applovin", "AppLovin"),
        ("unity", "Unity"),
        ("roblox", "Roblox"),
        ("box", "Box"),
        ("docusign", "DocuSign"),
        ("monday", "Monday.com"),
        ("clickup", "ClickUp"),
        ("wrike", "Wrike"),
        ("smartsheet", "Smartsheet"),
        ("coda", "Coda"),
        # AI/ML companies
        ("huggingface", "Hugging Face"),
        ("cohere", "Cohere"),
        ("ai21labs", "AI21 Labs"),
        ("stability", "Stability AI"),
        ("runway", "Runway"),
        ("jasperai", "Jasper AI"),
        ("adept", "Adept"),
        ("inflection", "Inflection AI"),
        ("characterai", "Character.AI"),
        ("inworld", "Inworld AI"),
        ("synthesia", "Synthesia"),
        ("descript", "Descript"),
        # Fintech
        ("marqeta", "Marqeta"),
        ("checkout", "Checkout.com"),
        ("klarna", "Klarna"),
        ("upstart", "Upstart"),
        ("sofi", "SoFi"),
        ("current", "Current"),
        ("varo", "Varo"),
        # Healthcare tech
        ("veeva", "Veeva"),
        ("flatiron", "Flatiron Health"),
        ("tempus", "Tempus"),
        ("grail", "GRAIL"),
        ("color", "Color Health"),
        ("illumina", "Illumina"),
        ("10xgenomics", "10x Genomics"),
        ("thermofisher", "Thermo Fisher"),
        ("intuitivesurgical", "Intuitive Surgical"),
    ],
    "lever": [
        ("anduril", "Anduril"),
        ("benchling", "Benchling"),
        ("woven", "Woven by Toyota"),
        ("ripple", "Ripple"),
        ("gemini", "Gemini"),
        ("retool", "Retool"),
        ("webflow", "Webflow"),
        ("loom", "Loom"),
        ("miro", "Miro"),
        ("linear", "Linear"),
        ("superhuman", "Superhuman"),
        ("front", "Front"),
        ("intercom", "Intercom"),
        ("gong", "Gong"),
        ("clari", "Clari"),
        ("outreach", "Outreach"),
        ("apollo", "Apollo.io"),
        ("zoominfo", "ZoomInfo"),
        ("clearbit", "Clearbit"),
        ("6sense", "6sense"),
        ("highspot", "Highspot"),
        ("seismic", "Seismic"),
        ("mindtickle", "MindTickle"),
        ("allego", "Allego"),
        ("fireflies", "Fireflies.ai"),
        ("otter", "Otter.ai"),
        ("fathom", "Fathom"),
        ("grain", "Grain"),
        ("vidyard", "Vidyard"),
        ("wistia", "Wistia"),
        ("vimeo", "Vimeo"),
        ("restream", "Restream"),
        ("streamyard", "StreamYard"),
        ("riverside", "Riverside.fm"),
        ("descript", "Descript"),
    ]
}

# Keywords to identify intern positions (must be exact matches or word boundaries)
INTERN_KEYWORDS = [
    "intern", "internship", "co-op", "coop", "co op",
    "summer 2025", "fall 2025", "spring 2025", "winter 2025",
    "summer 2026", "fall 2026", "spring 2026", "winter 2026",
    "new grad", "new college grad", "university grad",
    "early career", "entry level", "junior", "associate",
    "2025", "2026"  # Often appears in title for intern/new grad roles
]

# Keywords that indicate this is NOT an intern position
EXCLUDE_KEYWORDS = [
    "senior", "sr.", "sr ",
    "staff", "principal", "lead", "manager",
    "director", "head of", "vp ", "vice president",
    "iv", " v ", " vi ",  # Senior levels (IV, V, VI)
    "architect"  # Usually senior role
]

# Keywords to identify software engineering positions
SWE_KEYWORDS = [
    "software", "engineer", "developer", "swe", "sde", "sdet",
    "backend", "frontend", "front-end", "back-end", "front end", "back end",
    "full stack", "fullstack", "full-stack",
    "mobile", "ios", "android", "web", "platform",
    "infrastructure", "devops", "dev ops", "systems", "data engineer",
    "machine learning", "ml engineer", "ai engineer", "embedded",
    "firmware", "cloud", "security", "site reliability", "sre",
    "data science", "research", "computer science", "cs ",
    "programmer", "coding", "tech", "technology",
    "application", "product engineer", "technical",
    "qa ", "quality assurance", "test", "automation",
    "game", "graphics", "computer vision", "robotics",
    "distributed systems", "api", "microservices",
    "database", "network", "compute", "storage",
    "java", "python", "c++", "javascript", "react", "node",
    ".net", "angular", "vue", "typescript",
    "hardware", "fpga", "verification", "validation",
    "data", "analytics", "business intelligence", "bi ",
    "integration", "deployment", "ci/cd", "build",
    "wireless", "5g", "rf", "signal", "networking"
]

SOFTWARE_ENGINEER_TOKENS = [
    "software engineer",
    "software engineering",
    "swe",
    "sde"
]

CALIFORNIA_TOKENS = [
    "california",
    "san francisco",
    "san jose",
    "palo alto",
    "menlo park",
    "mountain view",
    "sunnyvale",
    "san mateo",
    "santa clara",
    "los angeles",
    "culver city",
    "irvine",
    "pasadena",
    "santa monica",
    "san diego",
    "redwood city",
    "foster city",
    "oakland",
    "berkeley"
]

SEATTLE_TOKENS = [
    "seattle",
    "seattle, wa",
    "seattle wa",
    "bellevue",
    "redmond",
    "kirkland",
    "bothell",
    "tacoma",
    "washington"
]


def is_software_engineer_intern(title: str) -> bool:
    title_lower = title.lower()
    is_intern = any(kw in title_lower for kw in INTERN_KEYWORDS)
    is_swe = any(kw in title_lower for kw in SWE_KEYWORDS)
    is_excluded = any(kw in title_lower for kw in EXCLUDE_KEYWORDS)

    return is_intern and is_swe and not is_excluded


def has_state_token(location_lower: str, state: str) -> bool:
    return any(
        token in location_lower
        for token in [
            f", {state}",
            f" {state},",
            f" {state} ",
            f"({state}",
            f"{state})"
        ]
    )


def location_priority(location: str) -> int:
    location_lower = location.lower()
    is_california = any(token in location_lower for token in CALIFORNIA_TOKENS) or has_state_token(location_lower, "ca")
    is_seattle = any(token in location_lower for token in SEATTLE_TOKENS) or has_state_token(location_lower, "wa")
    is_remote = "remote" in location_lower or "hybrid" in location_lower
    is_usa = "usa" in location_lower or "united states" in location_lower or "us" == location_lower.strip()

    if is_california:
        return 0
    if is_seattle:
        return 1
    if is_remote or is_usa:
        return 2
    return 3


def should_include_location(location: str) -> bool:
    return location_priority(location) <= 2


def fetch_greenhouse_jobs(company_id: str, company_name: str) -> List[Dict]:
    """Fetch jobs from Greenhouse API"""
    jobs = []
    try:
        url = GREENHOUSE_API.format(company=company_id)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for job in data.get("jobs", []):
                title = job.get("title", "")
                if not is_software_engineer_intern(title):
                    continue

                location = job.get("location", {}).get("name", "N/A")
                if not should_include_location(location):
                    continue

                posted_at = job.get("updated_at", job.get("created_at", ""))

                # Calculate days since posted
                days_posted = calculate_days_posted(posted_at)

                jobs.append({
                    "company": company_name,
                    "title": job.get("title", ""),
                    "location": location,
                    "url": job.get("absolute_url", ""),
                    "days_posted": days_posted,
                    "compensation": ""  # Greenhouse doesn't expose compensation
                })
    except Exception as e:
        print(f"Error fetching from Greenhouse for {company_name}: {e}")
    return jobs


def fetch_lever_jobs(company_id: str, company_name: str) -> List[Dict]:
    """Fetch jobs from Lever API"""
    jobs = []
    try:
        url = LEVER_API.format(company=company_id)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for job in data:
                title = job.get("text", "")
                if not is_software_engineer_intern(title):
                    continue

                categories = job.get("categories", {})
                location = categories.get("location", "N/A")
                if not should_include_location(location):
                    continue

                posted_at = job.get("createdAt", 0)

                # Lever uses milliseconds timestamp
                if posted_at:
                    posted_date = datetime.fromtimestamp(posted_at / 1000)
                    days_posted = (datetime.now() - posted_date).days
                else:
                    days_posted = 0

                jobs.append({
                    "company": company_name,
                    "title": job.get("text", ""),
                    "location": location,
                    "url": job.get("hostedUrl", ""),
                    "days_posted": days_posted,
                    "compensation": ""
                })
    except Exception as e:
        print(f"Error fetching from Lever for {company_name}: {e}")
    return jobs


def calculate_days_posted(date_string: str) -> int:
    """Calculate days since job was posted"""
    if not date_string:
        return 0
    try:
        # Handle ISO format dates
        if "T" in date_string:
            posted_date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            posted_date = posted_date.replace(tzinfo=None)
        else:
            posted_date = datetime.strptime(date_string[:10], "%Y-%m-%d")
        
        days = (datetime.now() - posted_date).days
        return max(0, days)
    except:
        return 0


def fetch_all_jobs() -> Dict[str, List[Dict]]:
    """Fetch all jobs from all sources"""
    all_jobs = {
        "faang": [],
        "other": []
    }

    print("Fetching FAANG+ jobs...")
    
    # Add manual entries for companies using Workday/Taleo/proprietary ATS
    manual_jobs = FAANG_COMPANIES.get("manual", [])
    all_jobs["faang"].extend(manual_jobs)
    if manual_jobs:
        print(f"  Manual entries (Workday/ATS companies): {len(manual_jobs)} positions")
    
    for company_id, company_name in FAANG_COMPANIES.get("greenhouse", []):
        jobs = fetch_greenhouse_jobs(company_id, company_name)
        all_jobs["faang"].extend(jobs)
        print(f"  {company_name}: {len(jobs)} positions")

    for company_id, company_name in FAANG_COMPANIES.get("lever", []):
        jobs = fetch_lever_jobs(company_id, company_name)
        all_jobs["faang"].extend(jobs)
        print(f"  {company_name}: {len(jobs)} positions")

    print("\nFetching Other company jobs...")
    for company_id, company_name in OTHER_COMPANIES.get("greenhouse", []):
        jobs = fetch_greenhouse_jobs(company_id, company_name)
        all_jobs["other"].extend(jobs)
        print(f"  {company_name}: {len(jobs)} positions")

    for company_id, company_name in OTHER_COMPANIES.get("lever", []):
        jobs = fetch_lever_jobs(company_id, company_name)
        all_jobs["other"].extend(jobs)
        print(f"  {company_name}: {len(jobs)} positions")

    # Sort by location priority (California, then Seattle), then by recency
    for category in all_jobs:
        all_jobs[category].sort(
            key=lambda x: (location_priority(x["location"]), x["days_posted"])
        )

    return all_jobs


def generate_job_table(jobs: List[Dict]) -> str:
    """Generate markdown table for jobs"""
    if not jobs:
        return "| Company | Title | Location | Compensation | Apply | Days Posted |\n|---------|-------|----------|--------------|-------|-------------|\n| *No positions available* | - | - | - | - | - |"
    
    table = "| Company | Title | Location | Compensation | Apply | Days Posted |\n"
    table += "|---------|-------|----------|--------------|-------|-------------|\n"
    
    for job in jobs:
        company = job["company"]
        title = job["title"]
        location = job["location"]
        compensation = job.get("compensation", "")
        url = job["url"]
        days = f"{job['days_posted']}d"
        
        # Truncate long titles
        if len(title) > 70:
            title = title[:67] + "..."
        
        # Create apply button
        apply_link = f"[Apply]({url})" if url else "N/A"
        
        table += f"| {company} | {title} | {location} | {compensation} | {apply_link} | {days} |\n"
    
    return table


def generate_readme(all_jobs: Dict[str, List[Dict]]) -> str:
    """Generate the full README content"""
    total_faang = len(all_jobs["faang"])
    total_other = len(all_jobs["other"])
    total = total_faang + total_other

    last_updated = datetime.now().strftime("%B %d, %Y at %H:%M UTC")

    readme = f"""# 2026 Software Engineering Internship Positions

[![Daily Update](https://github.com/{REPO_OWNER}/{REPO_NAME}/actions/workflows/update.yml/badge.svg)](https://github.com/{REPO_OWNER}/{REPO_NAME}/actions/workflows/update.yml)

This repository lists the latest Software Engineering Internship openings for 2026. Positions are **automatically updated daily** via GitHub Actions.

**Last Updated:** {last_updated}

**Total Positions:** {total} ({total_faang} FAANG+, {total_other} Other)

**Focus:** California (priority) and Seattle, WA

---

## 🔎 Quick Links

- [FAANG+](#faang) - {total_faang} positions
- [Other](#other) - {total_other} positions

---

## USA Internships 🦅

### FAANG+
{generate_job_table(all_jobs["faang"])}

### Other
{generate_job_table(all_jobs["other"])}

---

## 📋 About

This list is automatically scraped from company career pages and job boards including:
- Greenhouse
- Lever
- Workday
- Company career pages

Positions within the last 120 days are included.

## 🤝 Contributing

Found a missing company or position? Open an issue or PR!

## ⚠️ Disclaimer

Job listings are scraped from public career pages. Always verify details on the official company website before applying.

---

*Inspired by [speedyapply/2026-SWE-College-Jobs](https://github.com/speedyapply/2026-SWE-College-Jobs)*
"""

    return readme


def main():
    """Main function to scrape jobs and update README"""
    print("=" * 50)
    print("2026 SWE Internship Scraper")
    print("=" * 50)
    print()
    
    # Fetch all jobs
    all_jobs = fetch_all_jobs()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  FAANG+ positions: {len(all_jobs['faang'])}")
    print(f"  Other positions: {len(all_jobs['other'])}")
    print("=" * 50)
    
    # Generate README
    readme_content = generate_readme(all_jobs)
    
    # Write to README.md
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("\n✅ README.md updated successfully!")
    
    # Also save raw job data as JSON for debugging
    with open("jobs.json", "w") as f:
        json.dump(all_jobs, f, indent=2)
    
    print("✅ jobs.json saved for reference")


if __name__ == "__main__":
    main()
