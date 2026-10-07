import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
import time
import re
from .base_scraper import BaseScraper, JobPosting

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn Jobs (without authentication)"""

    def __init__(self, keywords: List[str], locations: List[str], days_back: int = 1, max_jobs: int = 50):
        super().__init__(keywords, locations, days_back)
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.max_jobs = max_jobs
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }

    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from LinkedIn"""
        all_jobs = []

        print(f"[LinkedIn] Starting scrape for keywords: {self.keywords[:3]}...")

        # LinkedIn allows searching without login for public jobs
        for keyword in self.keywords[:3]:  # Limit to avoid rate limiting
            for location in self.locations[:3]:
                try:
                    jobs = self._scrape_keyword_location(keyword, location)
                    all_jobs.extend(jobs)
                    time.sleep(3)  # Be polite with delays
                except Exception as e:
                    print(f"[LinkedIn] Error scraping '{keyword}' in '{location}': {str(e)}")
                    continue

        print(f"[LinkedIn] Found {len(all_jobs)} jobs")
        return all_jobs

    def _scrape_keyword_location(self, keyword: str, location: str) -> List[JobPosting]:
        """Scrape jobs for specific keyword and location"""
        jobs = []

        # LinkedIn job search parameters
        params = {
            'keywords': keyword,
            'location': location,
            'f_E': '1,2',  # Entry level and associate
            'f_TPR': 'r86400',  # Posted in last 24 hours
            'position': 1,
            'pageNum': 0
        }

        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find job cards
            job_cards = soup.find_all('div', class_='base-card')

            for card in job_cards[:self.max_jobs]:
                try:
                    job = self._parse_job_card(card)
                    if job and self._is_valid_job(job):
                        jobs.append(job)
                except Exception as e:
                    print(f"[LinkedIn] Error parsing job card: {str(e)}")
                    continue

        except requests.RequestException as e:
            print(f"[LinkedIn] Request error: {str(e)}")

        return jobs

    def _parse_job_card(self, card) -> JobPosting:
        """Parse individual job card"""
        try:
            # Title and URL
            title_elem = card.find('h3', class_='base-search-card__title')
            if not title_elem:
                return None

            title = self.clean_text(title_elem.get_text())

            link_elem = card.find('a', class_='base-card__full-link')
            url = link_elem.get('href', '') if link_elem else ''

            # Company
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            company = self.clean_text(company_elem.get_text()) if company_elem else "Unknown"

            # Location
            location_elem = card.find('span', class_='job-search-card__location')
            location = self.clean_text(location_elem.get_text()) if location_elem else "Not specified"

            # Posted date
            date_elem = card.find('time', class_=lambda c: c and 'job-search-card__listdate' in c)
            posted_text = self.clean_text(date_elem.get_text()).lower() if date_elem else ""
            posted_date = date_elem.get('datetime', '') if date_elem else ""

            # Check for older than 24h in text
            if any(term in posted_text for term in ['2 days ago', '3 days ago', 'week', 'month']):
                posted_date = "OLD"
            elif any(term in posted_text for term in ['hour', 'minute', 'today', 'just now']):
                posted_date = datetime.now().strftime('%Y-%m-%d')
            elif '1 day ago' in posted_text or 'yesterday' in posted_text:
                posted_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            elif posted_date:
                if 'T' in posted_date:
                    posted_date = posted_date.split('T')[0]
            else:
                posted_date = "UNKNOWN"

            return JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                posted_date=posted_date,
                description="",
                source="LinkedIn"
            )

        except Exception as e:
            print(f"[LinkedIn] Parse error: {str(e)}")
            return None

    def _is_valid_job(self, job: JobPosting) -> bool:
        """Check if job meets criteria"""
        # Strict 24-hour verification
        if not self.is_posted_within_24_hours(job.posted_date):
            return False

        # Check if technical and fresher-friendly
        if not self.is_technical_role(job.title, job.description):
            return False

        if not self.is_fresher_role(job.title, job.description):
            return False

        return True
