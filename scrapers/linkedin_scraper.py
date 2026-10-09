import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
import time
import re
from .base_scraper import BaseScraper, JobPosting

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn Jobs with strict 0-year fresher filtering"""

    def __init__(self, keywords: List[str] = None, locations: List[str] = None, days_back: int = 1, max_jobs: int = 50):
        super().__init__(keywords or [], locations or [], days_back)
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.max_jobs = max_jobs
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from LinkedIn strictly for 0 years experience / freshers"""
        all_jobs = []
        seen_urls = set()

        # Targeted search queries specifically targeting freshers and cybersecurity
        fresher_queries = [
            'fresher software engineer',
            'junior software developer',
            'associate software engineer',
            'cybersecurity fresher',
            'cyber security intern',
            'junior security analyst',
            'graduate engineer trainee',
            'entry level software developer'
        ]

        target_locations = self.locations[:3] if self.locations else ['India']
        print(f"[LinkedIn] Starting scrape for 0-exp fresher jobs & cybersecurity roles...")

        for query in fresher_queries[:5]:
            for location in target_locations:
                try:
                    jobs = self._scrape_keyword_location(query, location)
                    for job in jobs:
                        if job.url not in seen_urls:
                            seen_urls.add(job.url)
                            all_jobs.append(job)
                            if len(all_jobs) >= self.max_jobs:
                                break
                    if len(all_jobs) >= self.max_jobs:
                        break
                    time.sleep(2)
                except Exception as e:
                    print(f"[LinkedIn] Error scraping '{query}' in '{location}': {str(e)}")
                    continue
            if len(all_jobs) >= self.max_jobs:
                break

        print(f"[LinkedIn] Found {len(all_jobs)} strictly fresher/0-exp jobs")
        return all_jobs

    def _scrape_keyword_location(self, keyword: str, location: str) -> List[JobPosting]:
        """Scrape jobs for specific keyword and location"""
        jobs = []

        # LinkedIn parameters: f_E=1,2 (Internship, Entry level), f_TPR=r86400 (last 24h)
        params = {
            'keywords': keyword,
            'location': location,
            'f_E': '1,2',
            'f_TPR': 'r86400',
            'position': 1,
            'pageNum': 0
        }

        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=12)
            if response.status_code != 200:
                return jobs

            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')

            for card in job_cards[:self.max_jobs]:
                try:
                    job = self._parse_job_card(card)
                    if job and self._is_valid_job(job):
                        jobs.append(job)
                except Exception as e:
                    continue

        except requests.RequestException as e:
            print(f"[LinkedIn] Request error for '{keyword}': {str(e)}")

        return jobs

    def _parse_job_card(self, card) -> JobPosting:
        """Parse individual job card with strict fresher verification"""
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

            # Description placeholder / snippet
            snippet_elem = card.find('div', class_=lambda c: c and 'snippet' in c)
            description = self.clean_text(snippet_elem.get_text()) if snippet_elem else ""

            return JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                posted_date=posted_date,
                description=description,
                source="LinkedIn"
            )

        except Exception as e:
            return None

    def _is_valid_job(self, job: JobPosting) -> bool:
        """Check if job strictly meets 0-year fresher criteria"""
        # Strict 24-hour verification
        if not self.is_posted_within_24_hours(job.posted_date):
            return False

        # Technical / Cybersecurity role check
        if not self.is_technical_role(job.title, job.description):
            return False

        # Strict fresher verification (rejects any II, III, Sr, Lead, >0 yrs)
        if not self.is_fresher_role(job.title, job.description):
            return False

        return True
