from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict
import re

class JobPosting:
    """Represents a single job posting"""
    def __init__(self, title, company, location, url, posted_date, description="", source=""):
        self.title = title
        self.company = company
        self.location = location
        self.url = url
        self.posted_date = posted_date
        self.description = description
        self.source = source
        self.id = self._generate_id()

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
            'source': self.source
        }

class BaseScraper(ABC):
    """Base class for all job scrapers"""

    def __init__(self, keywords: List[str], locations: List[str], days_back: int = 1):
        self.keywords = [k.strip().lower() for k in keywords]
        self.locations = [l.strip() for l in locations]
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)

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
