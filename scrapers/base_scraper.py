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
    "siemens": "https://jobs.siemens.com/careers"
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

    def is_technical_role(self, title: str, description: str = "") -> bool:
        """Check if the job is a technical/CS role"""
        technical_keywords = [
            'software', 'developer', 'engineer', 'programmer', 'python', 'java',
            'javascript', 'react', 'angular', 'node', 'backend', 'frontend',
            'full stack', 'fullstack', 'data', 'machine learning', 'ml', 'ai',
            'devops', 'cloud', 'aws', 'azure', 'database', 'sql', 'android',
            'ios', 'mobile', 'web', 'api', 'tech', 'sde', 'swe', 'qa', 'test'
        ]

        # Exclude non-technical roles
        exclude_keywords = [
            'sales', 'marketing', 'manager', 'hr', 'recruiter', 'business development',
            'content writer', 'graphic design', 'accountant', 'finance', 'operations'
        ]

        text = (title + " " + description).lower()

        # Check exclusions first
        for exclude in exclude_keywords:
            if exclude in text:
                return False

        # Check if it's technical
        for keyword in technical_keywords:
            if keyword in text:
                return True

        return False

    def is_fresher_role(self, title: str, description: str = "") -> bool:
        """Check if the job is suitable for freshers"""
        text = (title + " " + description).lower()

        # Positive indicators for fresher roles
        fresher_indicators = [
            'fresher', 'entry level', 'entry-level', 'graduate', 'trainee',
            '0-1 year', '0-2 year', '0 year', 'recent graduate', 'new grad',
            'junior', 'associate', 'beginner'
        ]

        # Check for fresher indicators
        for indicator in fresher_indicators:
            if indicator in text:
                return True

        # Check for experience requirements that exclude freshers
        senior_indicators = [
            '3+ years', '4+ years', '5+ years', 'senior', 'lead', 'principal',
            'staff engineer', 'architect'
        ]

        for indicator in senior_indicators:
            if indicator in text:
                return False

        # If no clear indication, assume it might be suitable
        return True

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
