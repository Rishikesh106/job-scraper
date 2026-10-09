import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
import time
import re
from .base_scraper import BaseScraper, JobPosting

class IntershalaScraper(BaseScraper):
    """Scraper for Internshala (strictly 0 years experience / freshers & tech/cybersecurity internships)"""

    def __init__(self, keywords: List[str], locations: List[str], days_back: int = 1, max_jobs: int = 50):
        super().__init__(keywords, locations, days_back)
        self.base_url = "https://internshala.com"
        self.max_jobs = max_jobs
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from Internshala"""
        all_jobs = []
        seen_urls = set()

        # Internshala specific slugs for tech & cybersecurity
        search_slugs = [
            ('jobs', 'cyber-security'),
            ('jobs', 'software-development'),
            ('jobs', 'python'),
            ('jobs', 'data-science'),
            ('jobs', 'information-security'),
            ('internships', 'cyber-security'),
            ('internships', 'computer-science'),
            ('internships', 'python-django'),
            ('jobs', 'fresher')
        ]

        print(f"[Internshala] Starting scrape for 0-exp fresher jobs & cybersecurity roles...")

        for category, slug in search_slugs:
            try:
                jobs = self._scrape_slug(category, slug)
                for job in jobs:
                    if job.url not in seen_urls:
                        seen_urls.add(job.url)
                        all_jobs.append(job)
                        if len(all_jobs) >= self.max_jobs:
                            break
                if len(all_jobs) >= self.max_jobs:
                    break
                time.sleep(1.5)
            except Exception as e:
                print(f"[Internshala] Error scraping '{slug}': {str(e)}")
                continue

        print(f"[Internshala] Found {len(all_jobs)} strictly fresher/0-exp jobs")
        return all_jobs

    def _scrape_slug(self, category: str, slug: str) -> List[JobPosting]:
        """Scrape jobs or internships for a specific slug"""
        jobs = []
        if category == 'jobs':
            url = f"{self.base_url}/jobs/{slug}-jobs"
        else:
            url = f"{self.base_url}/internships/{slug}-internship"

        try:
            response = requests.get(url, headers=self.headers, timeout=12)
            if response.status_code != 200:
                return jobs

            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='individual_internship')

            for card in job_cards[:self.max_jobs]:
                try:
                    job = self._parse_job_card(card, category)
                    if job and self._is_valid_job(job):
                        jobs.append(job)
                except Exception as e:
                    continue

        except requests.RequestException as e:
            print(f"[Internshala] Request error for '{slug}': {str(e)}")

        return jobs

    def _parse_job_card(self, card, category: str = 'jobs') -> JobPosting:
        """Parse individual job card with strict experience verification"""
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

            # Experience field extraction from briefcase icon
            exp_i = card.find('i', class_=lambda c: c and 'briefcase' in c)
            experience = self.clean_text(exp_i.parent.get_text()) if exp_i else ""

            # STRICT REJECTION: If experience requires 1 or more years, reject immediately
            if experience and re.search(r'\b([1-9]\d*)\s*year\(s\)', experience, re.I):
                return None

            # Description/Tags
            desc_parts = []
            if experience:
                desc_parts.append(f"Experience: {experience}")
            elif category == 'internships':
                desc_parts.append("Internship (0 years experience / Student / Fresher)")

            skills_elem = card.find('div', class_=lambda c: c and any(k in c for k in ['job_skills', 'tags_container', 'skill_container']))
            if skills_elem:
                desc_parts.append(self.clean_text(skills_elem.get_text()))

            description = " | ".join(desc_parts)

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

        # Technical / Cybersecurity role check
        if not self.is_technical_role(job.title, job.description):
            return False

        # Strict fresher / 0 years check
        if not self.is_fresher_role(job.title, job.description, experience_text=job.description):
            return False

        return True
