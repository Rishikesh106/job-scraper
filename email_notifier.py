import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime
from scrapers.base_scraper import JobPosting

class EmailNotifier:
    """Handles email notifications for job alerts"""

    def __init__(self, sender_email: str, sender_password: str, receiver_email: str):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_job_alert(self, jobs: List[JobPosting]) -> bool:
        """Send email with job listings"""
        if not jobs:
            print("[Email] No jobs to send")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = f"🎯 {len(jobs)} New Tech Jobs for You - {datetime.now().strftime('%B %d, %Y')}"

            # Create HTML email
            html_content = self._create_html_email(jobs)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"[Email] Successfully sent email with {len(jobs)} jobs")
            return True

        except Exception as e:
            print(f"[Email] Error sending email: {str(e)}")
            return False

    def _create_html_email(self, jobs: List[JobPosting]) -> str:
        """Create HTML formatted email"""
        # Group jobs by source
        jobs_by_source = {}
        for job in jobs:
            source = job.source or "Other"
            if source not in jobs_by_source:
                jobs_by_source[source] = []
            jobs_by_source[source].append(job)

        # HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .stats {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stats h2 {{
                    margin: 0;
                    color: #667eea;
                    font-size: 36px;
                }}
                .stats p {{
                    margin: 5px 0 0 0;
                    color: #666;
                }}
                .source-section {{
                    margin-bottom: 30px;
                }}
                .source-header {{
                    background: #667eea;
                    color: white;
                    padding: 15px 20px;
                    border-radius: 8px 8px 0 0;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .job-card {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-top: none;
                    padding: 20px;
                    margin-bottom: 0;
                    transition: transform 0.2s;
                }}
                .job-card:last-child {{
                    border-radius: 0 0 8px 8px;
                }}
                .job-card:hover {{
                    background: #f9f9f9;
                }}
                .job-title {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 0 0 10px 0;
                }}
                .job-title a {{
                    color: #667eea;
                    text-decoration: none;
                }}
                .job-title a:hover {{
                    text-decoration: underline;
                }}
                .job-company {{
                    font-size: 16px;
                    color: #555;
                    margin: 5px 0;
                    font-weight: 500;
                }}
                .job-details {{
                    color: #777;
                    font-size: 14px;
                    margin: 5px 0;
                }}
                .job-location {{
                    display: inline-block;
                    margin-right: 15px;
                }}
                .job-date {{
                    display: inline-block;
                    color: #27ae60;
                    font-weight: 500;
                }}
                .apply-btn {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 10px 25px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 15px;
                    font-weight: bold;
                    transition: transform 0.2s;
                }}
                .apply-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding: 20px;
                    background: white;
                    border-radius: 8px;
                    color: #666;
                    font-size: 14px;
                }}
                .emoji {{
                    font-size: 24px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Your Daily Tech Job Alert</h1>
                <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
            </div>

            <div class="stats">
                <h2>{len(jobs)}</h2>
                <p>New opportunities found in the last 24 hours</p>
            </div>
        """

        # Add jobs grouped by source
        for source, source_jobs in jobs_by_source.items():
            html += f"""
            <div class="source-section">
                <div class="source-header">
                    {source} ({len(source_jobs)} jobs)
                </div>
            """

            for job in source_jobs:
                html += f"""
                <div class="job-card">
                    <div class="job-title">
                        <a href="{job.url}" target="_blank">{job.title}</a>
                    </div>
                    <div class="job-company">🏢 {job.company}</div>
                    <div class="job-details">
                        <span class="job-location">📍 {job.location}</span>
                        <span class="job-date">🕒 Posted: {job.posted_date}</span>
                    </div>
                    <a href="{job.url}" target="_blank" class="apply-btn">Apply Now →</a>
                </div>
                """

            html += "</div>"

        # Footer
        html += """
            <div class="footer">
                <p><strong>💡 Pro Tips for Success:</strong></p>
                <p>✅ Apply within 24 hours for better visibility<br>
                ✅ Customize your resume for each role<br>
                ✅ Follow up after applying<br>
                ✅ Network with employees at target companies</p>
                <p style="margin-top: 20px; color: #999;">
                    This is an automated job alert. You're receiving this because you subscribed to daily tech job notifications.
                </p>
            </div>
        </body>
        </html>
        """

        return html

    def send_error_notification(self, error_message: str) -> bool:
        """Send email notification about scraping errors"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = "⚠️ Job Scraper Error Alert"

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #e74c3c;">Job Scraper Error</h2>
                <p>The job scraper encountered an error:</p>
                <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #e74c3c;">
                    <code>{error_message}</code>
                </div>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"[Email] Error sending error notification: {str(e)}")
            return False
