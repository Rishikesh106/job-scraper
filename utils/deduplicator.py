from typing import List, Set
from scrapers.base_scraper import JobPosting
import json
from datetime import datetime, timedelta
import os

class JobDeduplicator:
    """Handles deduplication of job postings"""

    def __init__(self, cache_file: str = "jobs_cache.json"):
        self.cache_file = cache_file
        self.seen_ids: Set[int] = set()
        self.load_cache()

    def load_cache(self):
        """Load previously seen job IDs from cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Remove jobs older than 7 days from cache
                    cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    for job_data in data:
                        if job_data.get('posted_date', '') >= cutoff:
                            self.seen_ids.add(job_data['id'])
                print(f"[Deduplicator] Loaded {len(self.seen_ids)} jobs from cache")
            except Exception as e:
                print(f"[Deduplicator] Error loading cache: {str(e)}")

    def save_cache(self, jobs: List[JobPosting]):
        """Save current jobs to cache"""
        try:
            # Combine new jobs with recent cached jobs
            all_jobs_dict = {}

            # Load existing cache
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                        cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                        for job in existing:
                            if job.get('posted_date', '') >= cutoff:
                                all_jobs_dict[job['id']] = job
                except:
                    pass

            # Add new jobs
            for job in jobs:
                all_jobs_dict[job.id] = job.to_dict()

            # Save to file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(list(all_jobs_dict.values()), f, indent=2, ensure_ascii=False)

            print(f"[Deduplicator] Saved {len(all_jobs_dict)} jobs to cache")
        except Exception as e:
            print(f"[Deduplicator] Error saving cache: {str(e)}")

    def deduplicate(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Remove duplicate jobs and jobs already seen"""
        unique_jobs = []
        new_count = 0

        for job in jobs:
            if job.id not in self.seen_ids:
                unique_jobs.append(job)
                self.seen_ids.add(job.id)
                new_count += 1

        print(f"[Deduplicator] {new_count} new jobs out of {len(jobs)} total")
        return unique_jobs

    def filter_by_quality(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Filter out low-quality or suspicious job postings"""
        quality_jobs = []

        for job in jobs:
            # Skip if essential fields are missing
            if not job.title or not job.company or not job.url:
                continue

            # Skip if company name looks suspicious
            suspicious_companies = ['test company', 'xyz company', 'abc corp', 'unknown']
            if any(sus in job.company.lower() for sus in suspicious_companies):
                continue

            # Skip if title is too short or generic
            if len(job.title) < 5:
                continue

            quality_jobs.append(job)

        removed = len(jobs) - len(quality_jobs)
        if removed > 0:
            print(f"[Deduplicator] Filtered out {removed} low-quality jobs")

        return quality_jobs
