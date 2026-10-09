from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict
import re
import urllib.parse

# Known direct career portals for popular tech employers
KNOWN_CAREER_PORTALS = {
    "google": "https://careers.google.com/jobs/results/",
    "microsoft": "https://careers.microsoft.com/professionals/us/en/search-results",
    "amazon": "https://www.amazon.jobs/en/search",
    "meta": "https://www.metacareers.com/jobs",
    "facebook": "https://www.metacareers.com/jobs",
    "apple": "https://jobs.apple.com/en-us/search",
    "netflix": "https://jobs.netflix.com/search",
    "uber": "https://www.uber.com/careers/list/",
    "tcs": "https://www.tcs.com/careers/india",
    "tata consultancy services": "https://www.tcs.com/careers/india",
    "infosys": "https://www.infosys.com/careers.html",
    "wipro": "https://careers.wipro.com/",
    "accenture": "https://www.accenture.com/in-en/careers/jobsearch",
    "cognizant": "https://careers.cognizant.com/global/en",
    "capgemini": "https://www.capgemini.com/careers/",
    "hcl": "https://www.hcltech.com/careers",
    "hcl tech": "https://www.hcltech.com/careers",
    "tech mahindra": "https://careers.techmahindra.com/",
    "swiggy": "https://careers.swiggy.com/",
    "zomato": "https://www.zomato.com/careers",
    "flipkart": "https://www.flipkartcareers.com/",
    "paytm": "https://paytm.com/careers",
    "phonepe": "https://www.phonepe.com/careers/",
    "razorpay": "https://razorpay.com/jobs/",
    "oracle": "https://www.oracle.com/corporate/careers/",
    "ibm": "https://www.ibm.com/careers",
    "cisco": "https://jobs.cisco.com/",
    "intel": "https://jobs.intel.com/",
    "nvidia": "https://www.nvidia.com/en-us/about-nvidia/careers/",
    "salesforce": "https://www.salesforce.com/company/careers/",
    "adobe": "https://www.adobe.com/careers.html",
    "deloitte": "https://jobsindia.deloitte.com/",
    "ey": "https://www.ey.com/en_gl/careers",
    "pwc": "https://www.pwc.in/careers.html",
    "kpmg": "https://kpmg.com/in/en/home/careers.html",
    "jpmorgan": "https://careers.jpmorgan.com/",
    "jp morgan": "https://careers.jpmorgan.com/",
    "goldman sachs": "https://www.goldmansachs.com/careers/",
    "morgan stanley": "https://www.morganstanley.com/people-opportunities/careers",
    "wells fargo": "https://www.wellsfargojobs.com/",
    "sap": "https://jobs.sap.com/",
    "siemens": "https://jobs.siemens.com/careers",
    "palo alto networks": "https://jobs.paloaltonetworks.com/en/",
    "crowdstrike": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers",
    "fortinet": "https://www.fortinet.com/corporate/careers",
    "zscaler": "https://www.zscaler.com/careers",
    "qualys": "https://www.qualys.com/company/careers/",
    "rapid7": "https://www.rapid7.com/about/careers/",
    "splunk": "https://www.splunk.com/en_us/careers.html",
    "checkpoint": "https://careers.checkpoint.com/",
    "mandiant": "https://www.mandiant.com/company/careers"
}

class JobPosting:
    """Represents a single job posting"""
    def __init__(self, title, company, location, url, posted_date, description="", source="", company_careers_url=""):
        self.title = title
        self.company = company
        self.location = location
        self.url = url
        self.posted_date = posted_date
        self.description = description
        self.source = source
        self.company_careers_url = company_careers_url or self._generate_careers_url()
        self.id = self._generate_id()

    def _generate_careers_url(self) -> str:
        """Generate a direct link to the company's official career page"""
        if not self.company or self.company.lower() in ['unknown', 'not specified']:
            return self.url

        clean_name = self.company.lower().strip()
        # Clean suffixes like Pvt Ltd, Ltd, Technologies, Inc
        clean_name = re.sub(r'\b(pvt|ltd|limited|private limited|technologies|solutions|services|inc|corp|corporation|llc)\b', '', clean_name, flags=re.IGNORECASE).strip()

        # Check known portals
        for known_key, portal_url in KNOWN_CAREER_PORTALS.items():
            if known_key in clean_name or clean_name in known_key:
                return portal_url

        # Otherwise, generate a targeted Google Careers direct search query
        company_query = re.sub(r'[^a-zA-Z0-9\s]', '', self.company).strip()
        query = f"{company_query} official career page jobs {self.title}"
        return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"

    def _generate_id(self):
        """Generate unique ID based on title, company, and URL"""
        key = f"{self.title}_{self.company}_{self.url}".lower()
        return hash(key)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'posted_date': self.posted_date,
            'description': self.description,
            'source': self.source,
            'company_careers_url': self.company_careers_url
        }

class BaseScraper(ABC):
    """Base class for all job scrapers"""

    def __init__(self, keywords: List[str], locations: List[str], days_back: int = 1):
        self.keywords = [k.strip().lower() for k in keywords]
        self.locations = [l.strip() for l in locations]
        self.days_back = days_back
        # Strict 24 hour cutoff (1 day)
        self.cutoff_date = datetime.now() - timedelta(days=1)

    def is_posted_within_24_hours(self, posted_date_str: str) -> bool:
        """Strictly verify if job was posted within the last 24 hours"""
        if not posted_date_str or posted_date_str in ['OLD', 'UNKNOWN', 'unknown']:
            return False

        try:
            # Check YYYY-MM-DD
            job_date = datetime.strptime(posted_date_str, '%Y-%m-%d')
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            # Only today or yesterday is within 24 hours
            return job_date.date() in [today, yesterday]
        except Exception:
            return False

    @abstractmethod
    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from the source. Must be implemented by subclasses."""
        pass

    @staticmethod
    def is_technical_role(title: str, description: str = "") -> bool:
        """Check if the job is a technical/CS or Cybersecurity role"""
        technical_keywords = [
            # Software Development & Engineering
            'software', 'developer', 'engineer', 'programmer', 'python', 'java',
            'javascript', 'typescript', 'react', 'angular', 'vue', 'node', 'nodejs',
            'backend', 'frontend', 'full stack', 'fullstack', 'web development', 'web developer',
            'sde', 'swe', 'mobile developer', 'android', 'ios', 'flutter',
            # Data, AI & Machine Learning
            'data analyst', 'data engineer', 'data science', 'machine learning', 'ml', 'ai', 'artificial intelligence',
            # DevOps, Cloud & QA
            'devops', 'cloud', 'aws', 'azure', 'gcp', 'database', 'sql', 'qa', 'test engineer', 'quality assurance',
            # Cybersecurity & Information Security
            'cyber', 'cybersecurity', 'cyber security', 'infosec', 'information security',
            'security analyst', 'security engineer', 'soc analyst', 'soc', 'vulnerability',
            'penetration tester', 'pentest', 'ethical hacker', 'network security',
            'incident response', 'iam', 'identity and access', 'threat', 'appsec', 'application security',
            'devsecops', 'siem'
        ]

        title_lower = title.lower()
        text_lower = (title + " " + description).lower()

        # Non-tech roles to explicitly exclude regardless of company description
        non_tech_roles = [
            'accounts receivable', 'accounts payable', 'accounting', 'accountant', 'finance',
            'sales executive', 'sales manager', 'sales representative', 'telecaller', 'bpo',
            'customer support', 'customer service', 'customer success', 'hr executive',
            'recruiter', 'office manager', 'executive assistant', 'content writer', 'graphic designer'
        ]
        for nt in non_tech_roles:
            if nt in title_lower and not any(k in title_lower for k in ['developer', 'engineer', 'security', 'cyber', 'programmer']):
                return False

        # 1. Match technical keywords directly in the title with word boundaries
        for keyword in technical_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', title_lower):
                return True

        # 2. Match role indicator in title + technical keywords in description
        role_indicators = ['developer', 'engineer', 'programmer', 'coder', 'sde', 'swe', 'security']
        if any(re.search(r'\b' + re.escape(r) + r'\b', title_lower) for r in role_indicators):
            for keyword in technical_keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    return True

        return False

    @staticmethod
    def is_fresher_role(title: str, description: str = "", experience_text: str = "", min_years: int = None) -> bool:
        """Strictly verify if the job is for 0 years experience or freshers only"""
        # 1. If explicit numeric min_years is provided
        if min_years is not None:
            if min_years > 0:
                return False

        title_clean = title.strip()
        full_text = f"{title_clean} {experience_text} {description}".lower()

        # 2. Strict Senior / Non-Fresher Exclusions in Title
        # Exclude Roman numerals II, III, IV, V or numbers 2, 3, 4, 5 denoting non-entry levels
        # (Note: I / 1 / Trainee / Junior / Associate / GET are entry levels)
        if re.search(r'\b(ii|iii|iv|v|vi|2|3|4|5)\b', title_clean, re.I):
            return False

        # Exclude senior and management keywords in title
        senior_title_pattern = r'\b(sr|sr\.|senior|lead|principal|staff|architect|manager|head|director|vp|vice president|specialist|experienced|mid-level|mid level|intermediate|expert|team lead|tech lead)\b'
        if re.search(senior_title_pattern, title_clean, re.I):
            return False

        # 3. Check for Experience Requirements > 0 anywhere in text
        # Reject e.g., "1+ years", "2+ yrs", "3+ years", "1 to 3 years", "1-3 years", "2-5 yrs", "min 1 year"
        if re.search(r'\b([1-9]\d*)\s*(?:\+|plus)\s*(?:years?|yrs?)', full_text):
            return False
        if re.search(r'\b([1-9]\d*)\s*(?:to|-)\s*\d+\s*(?:years?|yrs?)', full_text):
            return False
        if re.search(r'\b(?:min|minimum|at least)\s*([1-9]\d*)\s*(?:years?|yrs?)', full_text):
            return False
        if re.search(r'\b([1-9]\d*)\s*(?:years?|yrs?)\s*(?:of\s*)?experience', full_text):
            return False
        if re.search(r'\b([1-9]\d*)\s*year\(s\)', full_text):
            return False

        # 4. If min_years was explicitly confirmed as 0
        if min_years == 0:
            return True

        # 5. Positive Fresher / 0 Years Indicators
        fresher_indicators = [
            r'\bfresher\b', r'\bfreshers\b',
            r'\bentry\s*level\b', r'\bentry-level\b',
            r'\bgraduate\b', r'\bgraduate\s+engineer\s+trainee\b', r'\bget\b',
            r'\btrainee\b', r'\bintern\b', r'\binternship\b',
            r'\bassociate\b', r'\bjunior\b', r'\bjr\b', r'\bjr\.\b',
            r'\bapprentice\b', r'\bapprenticeship\b',
            r'\b0\s*years?\b', r'\b0-0\s*years?\b', r'\b0-1\s*years?\b', r'\b0\s*to\s*1\s*years?\b',
            r'\b0\s*yrs?\b', r'\b0-0\s*yrs?\b', r'\b0-1\s*yrs?\b',
            r'\bno\s*experience\s*required\b', r'\bno\s*prior\s*experience\b',
            r'\brecent\s*graduate\b', r'\bnew\s*grad\b', r'\bcollege\s*graduate\b',
            r'\bcampus\b', r'\b2024\s*batch\b', r'\b2025\s*batch\b', r'\b2026\s*batch\b',
            r'\bbatch\s*of\s*2024\b', r'\bbatch\s*of\s*2025\b', r'\bbatch\s*of\s*2026\b'
        ]

        for pattern in fresher_indicators:
            if re.search(pattern, full_text):
                return True

        # STRICT: If no clear fresher indicator, REJECT
        return False

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
