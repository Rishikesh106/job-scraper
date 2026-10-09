import requests
import bs4
import json
from datetime import datetime, timedelta
import re
from typing import List
from .base_scraper import BaseScraper, JobPosting

class WellfoundScraper(BaseScraper):
    """
    Scraper for Wellfound (formerly AngelList Talent).
    Specializes in startup roles where companies have high response rates.
    """

    def __init__(self, keywords: List[str] = None, locations: List[str] = None, days_back: int = 1, max_jobs: int = 50):
        super().__init__(keywords or [], locations or [], days_back)
        self.max_jobs = max_jobs
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }

    def scrape(self) -> List[JobPosting]:
        """Scrape jobs from Wellfound"""
        all_jobs = []
        print("[Wellfound] Starting scrape for entry-level / fresher tech & cybersecurity jobs...")

        # Wellfound clean public role pages for tech & cybersecurity
        urls = [
            'https://wellfound.com/role/l/software-engineer/india',
            'https://wellfound.com/role/l/security-engineer/india',
            'https://wellfound.com/role/l/cybersecurity-engineer/india',
            'https://wellfound.com/role/l/frontend-engineer/india',
            'https://wellfound.com/role/l/backend-engineer/india',
            'https://wellfound.com/role/l/full-stack-engineer/india',
            'https://wellfound.com/role/l/data-analyst/india',
            'https://wellfound.com/role/l/security-engineer/remote',
            'https://wellfound.com/role/l/software-engineer/remote',
            'https://wellfound.com/jobs',
        ]

        seen_urls = set()

        for url in urls:
            try:
                jobs = self._scrape_url(url)
                for job in jobs:
                    if job.url not in seen_urls:
                        seen_urls.add(job.url)
                        all_jobs.append(job)
                        if len(all_jobs) >= self.max_jobs:
                            break
                if len(all_jobs) >= self.max_jobs:
                    break
            except Exception as e:
                print(f"[Wellfound] Error scraping {url}: {e}")
                continue

        print(f"[Wellfound] Found {len(all_jobs)} strictly fresher/0-exp jobs")
        return all_jobs

    def _scrape_url(self, url: str) -> List[JobPosting]:
        """Scrape and parse jobs from a Wellfound page"""
        jobs = []
        try:
            r = requests.get(url, headers=self.headers, timeout=12)
            if r.status_code != 200:
                return jobs

            soup = bs4.BeautifulSoup(r.content, 'html.parser')
            tag = soup.find('script', id='__NEXT_DATA__')
            if not tag or not tag.string:
                return jobs

            data = json.loads(tag.string)
            apollo = data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
            if not apollo:
                return jobs

            # Build startup mapping (StartupResult -> job refs)
            job_to_startup = {}
            for k, v in apollo.items():
                if isinstance(v, dict) and v.get('__typename') == 'StartupResult':
                    for jl in v.get('highlightedJobListings', []):
                        ref = jl.get('__ref')
                        if ref:
                            job_to_startup[ref] = v

            for k, v in apollo.items():
                if not isinstance(v, dict):
                    continue

                typename = v.get('__typename')
                if typename not in ['JobListingSearchResult', 'JobListing']:
                    continue

                title = v.get('title', '')
                if not title:
                    continue

                desc = v.get('description', '')
                min_exp = v.get('yearsExperienceMin')

                # Strict experience check (0 years / fresher only)
                if not self.is_fresher_role(title, desc, min_years=min_exp):
                    continue

                # Strict technical / cybersecurity check
                if not self.is_technical_role(title, desc):
                    continue

                # Check posted date
                live_start_at = v.get('liveStartAt')
                if live_start_at:
                    try:
                        posted_date = datetime.fromtimestamp(live_start_at).strftime('%Y-%m-%d')
                    except Exception:
                        posted_date = datetime.now().strftime('%Y-%m-%d')
                else:
                    posted_date = datetime.now().strftime('%Y-%m-%d')

                if not self.is_posted_within_24_hours(posted_date):
                    continue

                # Company name & details
                startup = job_to_startup.get(k)
                company = 'Unknown'
                if startup:
                    company = startup.get('name', 'Unknown')
                elif v.get('startup') and isinstance(v.get('startup'), dict):
                    ref = v['startup'].get('__ref')
                    if ref and ref in apollo:
                        company = apollo[ref].get('name', 'Unknown')

                # Job URL
                job_id = v.get('id', '')
                slug = v.get('slug', '')
                if job_id and slug:
                    job_url = f"https://wellfound.com/jobs/{job_id}-{slug}"
                elif job_id:
                    job_url = f"https://wellfound.com/jobs/{job_id}"
                else:
                    continue

                # Location
                locations = v.get('locationNames', [])
                if v.get('remote'):
                    locations.append('Remote')
                loc_str = ', '.join(locations) if locations else 'Remote / India'

                jobs.append(JobPosting(
                    title=title,
                    company=company,
                    location=loc_str,
                    url=job_url,
                    posted_date=posted_date,
                    description=desc[:500] if desc else f"Startup opportunity at {company} via Wellfound",
                    source="Wellfound"
                ))

        except Exception as e:
            print(f"[Wellfound] Parse error on {url}: {e}")

        return jobs
