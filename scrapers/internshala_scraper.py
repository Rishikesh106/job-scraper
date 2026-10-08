import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
import time
import re
from .base_scraper import BaseScraper, JobPosting

class IntershalaScraper(BaseScraper):
    """Scraper for Internshala (focuses on entry-level jobs)"""

    def __init__(self, keywords: List[str], locations: List[str], days_back: int = 1, max_jobs: int = 50):
        super().__init__(keywords, locations, days_back)
        self.base_url = "https://internshala.com"
        self.max_jobs = max_jobs
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }

    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from Internshala"""
        all_jobs = []

        print(f"[Internshala] Starting scrape for keywords: {self.keywords[:3]}...")

        # Internshala has both internships and fresher jobs
        for keyword in self.keywords[:3]:
            try:
                # Search for jobs (not internships)
                jobs = self._scrape_keyword(keyword, job_type='job')
                all_jobs.extend(jobs)
                time.sleep(2)
            except Exception as e:
                print(f"[Internshala] Error scraping '{keyword}': {str(e)}")
                continue

        print(f"[Internshala] Found {len(all_jobs)} jobs")
        return all_jobs

    def _scrape_keyword(self, keyword: str, job_type: str = 'job') -> List[JobPosting]:
        """Scrape jobs for a specific keyword"""
        jobs = []

        # Format keyword for URL
        keyword_formatted = keyword.replace(' ', '%20')

        # Internshala URL format for jobs
        url = f"{self.base_url}/jobs/{keyword_formatted}-jobs"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find job listings (Internshala uses specific div classes)
            job_cards = soup.find_all('div', class_='individual_internship')

            for card in job_cards[:self.max_jobs]:
                try:
                    job = self._parse_job_card(card)
                    if job and self._is_valid_job(job):
                        jobs.append(job)
                except Exception as e:
                    print(f"[Internshala] Error parsing job card: {str(e)}")
                    continue

        except requests.RequestException as e:
            print(f"[Internshala] Request error for '{keyword}': {str(e)}")

        return jobs

    def _parse_job_card(self, card) -> JobPosting:
        """Parse individual job card"""
        try:
            # Title and URL
            title_elem = card.find(['h2', 'h3'], class_='job-internship-name') or card.find('div', class_='job_name')
            if not title_elem:
                return None

            title_link = title_elem.find('a')
            if not title_link:
                return None

            title = self.clean_text(title_link.get_text())
            url = title_link.get('href', '')
            if not url:
                url = card.get('data-href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url

            # Company
            company_elem = card.find('p', class_='company-name') or card.find('div', class_='company_name') or card.find('a', class_='link_display_like_text')
            company = self.clean_text(company_elem.get_text()) if company_elem else "Unknown"

            # Location
            location_elem = card.find('p', class_=lambda c: c and 'locations' in c) or card.find('div', id=lambda x: x and 'location_names' in x) or card.find('span', class_='location_link')
            location = self.clean_text(location_elem.get_text()) if location_elem else "Not specified"

            # Posted date
            posted_elem = card.find('div', class_=lambda c: c and any(k in c for k in ['status-info', 'status-success', 'status']))
            posted_text = self.clean_text(posted_elem.get_text()) if posted_elem else ""
            posted_date = self._parse_date(posted_text)

            # Description/Tags
            desc_parts = []
            skills_elem = card.find('div', class_=lambda c: c and any(k in c for k in ['job_skills', 'tags_container', 'skill_container']))
            if skills_elem:
                desc_parts.append(self.clean_text(skills_elem.get_text()))

            description = " ".join(desc_parts)

            return JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                posted_date=posted_date,
                description=description,
                source="Internshala"
            )

        except Exception as e:
            print(f"[Internshala] Parse error: {str(e)}")
            return None

    def _parse_date(self, date_text: str) -> str:
        """Parse date from text"""
        date_text = date_text.lower().strip()

        # Reject explicitly older dates
        if any(term in date_text for term in ['2 days ago', '3 days ago', '4 days ago', '5 days ago', 'week', 'month']):
            return "OLD"

        days_match = re.search(r'(\d+)\s*days?\s*ago', date_text)
        if days_match and int(days_match.group(1)) >= 2:
            return "OLD"

        if 'today' in date_text or 'just now' in date_text or 'few hours ago' in date_text or 'hour' in date_text or 'minute' in date_text:
            return datetime.now().strftime('%Y-%m-%d')
        elif '1 day ago' in date_text or 'yesterday' in date_text:
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        return "UNKNOWN"

    def _is_valid_job(self, job: JobPosting) -> bool:
        """Check if job meets criteria"""
        # Strict 24-hour verification
        if not self.is_posted_within_24_hours(job.posted_date):
            return False

        # Internshala is already focused on freshers, but we still filter
        if not self.is_technical_role(job.title, job.description):
            return False

        return True
