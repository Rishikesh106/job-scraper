#!/usr/bin/env python3
"""
Main script to run the job scraper
"""
import os
import sys

# Ensure UTF-8 output on Windows consoles to handle emojis properly
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from scrapers import NaukriScraper, LinkedInScraper, IntershalaScraper
from utils import JobDeduplicator
from email_notifier import EmailNotifier

def main():
    """Main function to orchestrate job scraping"""
    print("=" * 60)
    print("🚀 Starting Job Scraper")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Get configuration with smart fallbacks
    sender_email = os.getenv('SENDER_EMAIL') or 'rishiauradkar@gmail.com'
    sender_password = os.getenv('SENDER_PASSWORD') or os.getenv('JOBSCRAPER')
    receiver_email = os.getenv('RECEIVER_EMAIL') or sender_email

    # Job search preferences with defaults
    raw_keywords = os.getenv('KEYWORDS')
    if raw_keywords and raw_keywords.strip():
        keywords = [k.strip() for k in raw_keywords.split(',') if k.strip()]
    else:
        keywords = [
            'software developer', 'software engineer', 'python developer',
            'full stack developer', 'backend developer', 'frontend developer',
            'data analyst', 'machine learning'
        ]

    raw_locations = os.getenv('LOCATIONS')
    if raw_locations and raw_locations.strip():
        locations = [l.strip() for l in raw_locations.split(',') if l.strip()]
    else:
        locations = [
            'India', 'Remote', 'Bangalore', 'Hyderabad',
            'Pune', 'Mumbai', 'Delhi', 'Noida', 'Gurgaon'
        ]

    days_back = int(os.getenv('DAYS_BACK', 1))
    max_jobs_per_source = int(os.getenv('MAX_JOBS_PER_SOURCE', 50))

    # Validate email configuration
    if not all([sender_email, sender_password, receiver_email]):
        print("❌ Error: Email configuration missing")
        print("Please provide SENDER_PASSWORD (or JOBSCRAPER secret)")
        sys.exit(1)

    print(f"\n📋 Configuration:")
    print(f"   Keywords: {len(keywords)} items")
    print(f"   Locations: {len(locations)} items")
    print(f"   Days back: {days_back}")
    print(f"   Max jobs per source: {max_jobs_per_source}")
    print()

    try:
        # Initialize scrapers
        scrapers = [
            NaukriScraper(keywords, locations, days_back, max_jobs_per_source),
            LinkedInScraper(keywords, locations, days_back, max_jobs_per_source),
            IntershalaScraper(keywords, locations, days_back, max_jobs_per_source),
        ]

        # Collect all jobs
        all_jobs = []
        for scraper in scrapers:
            try:
                print(f"\n🔍 Running {scraper.__class__.__name__}...")
                jobs = scraper.scrape()
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"❌ Error with {scraper.__class__.__name__}: {str(e)}")
                continue

        print(f"\n📊 Total jobs collected: {len(all_jobs)}")

        # Deduplicate and filter
        deduplicator = JobDeduplicator()

        # Filter by quality first
        quality_jobs = deduplicator.filter_by_quality(all_jobs)
        print(f"✅ Quality jobs: {len(quality_jobs)}")

        # Remove duplicates
        unique_jobs = deduplicator.deduplicate(quality_jobs)
        print(f"✨ New unique jobs: {len(unique_jobs)}")

        # Send email if there are new jobs
        if unique_jobs:
            print(f"\n📧 Sending email with {len(unique_jobs)} jobs...")
            notifier = EmailNotifier(sender_email, sender_password, receiver_email)

            if notifier.send_job_alert(unique_jobs):
                print("✅ Email sent successfully!")
                # Save to cache after successful email
                deduplicator.save_cache(unique_jobs)
            else:
                print("❌ Failed to send email")
                sys.exit(1)
        else:
            print("\n💤 No new jobs found today")
            print("📧 Sending daily status confirmation email...")
            notifier = EmailNotifier(sender_email, sender_password, receiver_email)
            notifier.send_no_jobs_notification(len(keywords), len(locations))

        print("\n" + "=" * 60)
        print("✅ Job scraper completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")

        # Try to send error notification
        try:
            notifier = EmailNotifier(sender_email, sender_password, receiver_email)
            notifier.send_error_notification(str(e))
        except:
            pass

        sys.exit(1)

if __name__ == "__main__":
    main()
