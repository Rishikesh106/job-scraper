import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
import time
import re
from .base_scraper import BaseScraper, JobPosting

class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com"""

    def __init__(self, keywords: List[str], locations: List[str], days_back: int = 1, max_jobs: int = 50):
        super().__init__(keywords, locations, days_back)
        self.base_url = "https://www.naukri.com"
        self.max_jobs = max_jobs
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }

    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from Naukri"""
        all_jobs = []

        print(f"[Naukri] Starting scrape for keywords: {self.keywords[:3]}...")

        for keyword in self.keywords[:5]:  # Limit to avoid rate limiting
            try:
                jobs = self._scrape_keyword(keyword)
                all_jobs.extend(jobs)
                time.sleep(2)  # Polite delay between requests
            except Exception as e:
                print(f"[Naukri] Error scraping keyword '{keyword}': {str(e)}")
                continue

        print(f"[Naukri] Found {len(all_jobs)} jobs")
        return all_jobs

    def _scrape_keyword(self, keyword: str) -> List[JobPosting]:
        """Scrape jobs for a specific keyword"""
        jobs = []

        # Format keyword for URL
        keyword_formatted = keyword.replace(' ', '-')

        # Naukri URL format
        url = f"{self.base_url}/{keyword_formatted}-jobs?experience=0"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find job listings
            job_cards = soup.find_all('article', class_='jobTuple')

            for card in job_cards[:self.max_jobs]:
                try:
                    job = self._parse_job_card(card)
                    if job and self._is_valid_job(job):
                        jobs.append(job)
                except Exception as e:
                    print(f"[Naukri] Error parsing job card: {str(e)}")
                    continue

        except requests.RequestException as e:
            print(f"[Naukri] Request error for '{keyword}': {str(e)}")

        return jobs

    def _parse_job_card(self, card) -> JobPosting:
        """Parse individual job card"""
        try:
            # Title and URL
            title_elem = card.find('a', class_='title')
            if not title_elem:
                return None

            title = self.clean_text(title_elem.get_text())
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url

            # Company
            company_elem = card.find('a', class_='subTitle')
            company = self.clean_text(company_elem.get_text()) if company_elem else "Unknown"

            # Location
            location_elem = card.find('li', class_='location')
            location = self.clean_text(location_elem.get_text()) if location_elem else "Not specified"

            # Experience
            exp_elem = card.find('li', class_='experience')
            experience = self.clean_text(exp_elem.get_text()) if exp_elem else ""

            # Posted date
            date_elem = card.find('span', class_='fleft')
            posted_text = self.clean_text(date_elem.get_text()) if date_elem else ""
            posted_date = self._parse_date(posted_text)

            # Description
            desc_elem = card.find('div', class_='job-description')
            description = self.clean_text(desc_elem.get_text()) if desc_elem else ""
            description += f" Experience: {experience}"

            return JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                posted_date=posted_date,
                description=description,
                source="Naukri"
            )

        except Exception as e:
            print(f"[Naukri] Parse error: {str(e)}")
            return None

    def _parse_date(self, date_text: str) -> str:
        """Parse date from text like 'Posted 1 day ago' or 'Posted today'"""
        date_text = date_text.lower()

        if 'today' in date_text or 'few hours ago' in date_text:
            return datetime.now().strftime('%Y-%m-%d')
        elif '1 day ago' in date_text or 'yesterday' in date_text:
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'days ago' in date_text:
            days = re.findall(r'(\d+)\s*days ago', date_text)
            if days:
                return (datetime.now() - timedelta(days=int(days[0]))).strftime('%Y-%m-%d')

        return datetime.now().strftime('%Y-%m-%d')

    def _is_valid_job(self, job: JobPosting) -> bool:
        """Check if job meets criteria"""
        # Check if technical and fresher-friendly
        if not self.is_technical_role(job.title, job.description):
            return False

        if not self.is_fresher_role(job.title, job.description):
            return False

        # Check date
        try:
            job_date = datetime.strptime(job.posted_date, '%Y-%m-%d')
            if job_date < self.cutoff_date:
                return False
        except:
            pass  # If date parsing fails, include the job

        return True
