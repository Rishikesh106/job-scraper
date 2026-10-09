# 🎯 Automated Job Scraper & Email Notifier

A Python-based job scraper that automatically finds fresh Computer Science, Tech, and Cybersecurity job openings strictly for freshers and candidates with 0 years of experience, emailing them to you daily.

## 🌟 Features

- **Multi-Platform Scraping**: Scrapes jobs from **Wellfound** (high response startup roles), **Internshala**, **LinkedIn**, and **Naukri**
- **Strict 0-Year Experience Filtering**: 
  - Strictly constricts to **0 years of experience / Freshers only** (actively blocks 1-5+ years experienced positions, Senior, II, III, Lead, etc.)
  - Dedicated support for **Cybersecurity** (SOC Analyst, Infosec, Security Engineer, Pen-testing) and **Tech/CS** roles
  - Posted within the last 24 hours
- **Deduplication**: Never see the same job twice
- **Beautiful Email Alerts**: Professional HTML emails with all job details and direct career page links
- **Automated Daily Run**: Set it and forget it with GitHub Actions
- **Quality Control**: Filters out spam, non-technical, and low-quality postings

## 📋 Prerequisites

- Python 3.8 or higher
- Gmail account (for sending emails)
- GitHub account (for automation)

## 🚀 Quick Start

### 1. Set Up Gmail App Password

Since this uses Gmail to send emails, you need an "App Password":

1. Go to your Google Account settings
2. Enable 2-Factor Authentication if not already enabled
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select "Mail" and "Other (Custom name)"
5. Name it "Job Scraper" and click Generate
6. **Copy the 16-character password** - you'll need it!

### 2. Local Setup (Test First)

```bash
# Clone or download this repository
cd job-scraper

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env file with your details
# Use any text editor to open .env and fill in:
# - SENDER_EMAIL: Your Gmail address
# - SENDER_PASSWORD: The app password you generated
# - RECEIVER_EMAIL: Your email (can be same as sender)
# - Customize KEYWORDS and LOCATIONS as needed
```

### 3. Test Run

```bash
# Run the scraper manually
python main.py
```

You should see output like:
```
🚀 Starting Job Scraper
📋 Configuration:
   Keywords: 8 items
   Locations: 9 items
🔍 Running NaukriScraper...
[Naukri] Found 15 jobs
...
✅ Email sent successfully!
```

Check your email - you should receive a beautiful formatted job listing!

## 🤖 Automated Daily Emails with GitHub Actions

Once you've tested locally and it works, set up automation:

### 1. Create GitHub Repository

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Job scraper"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/job-scraper.git
git branch -M main
git push -u origin main
```

### 2. Add GitHub Secrets

Go to your repository on GitHub:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these:

| Secret Name | Value |
|-------------|-------|
| `SENDER_EMAIL` | Your Gmail address |
| `SENDER_PASSWORD` | Your Gmail app password |
| `RECEIVER_EMAIL` | Your email (where you want to receive jobs) |
| `KEYWORDS` | `software developer,software engineer,python developer,full stack developer,backend developer,frontend developer,data analyst,machine learning` |
| `LOCATIONS` | `India,Remote,Bangalore,Hyderabad,Pune,Mumbai,Delhi,Noida,Gurgaon` |
| `EXPERIENCE_LEVEL` | `fresher,entry level,0-1 years,0-2 years` |

### 3. Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. You'll see "Daily Job Scraper" workflow
3. Click **Enable workflow** (if needed)
4. The workflow will run automatically every day at 6:00 AM UTC
5. You can also click **Run workflow** to test it immediately

### 4. Customize Schedule

The scraper runs at 6:00 AM UTC by default. To change this, edit `.github/workflows/daily-scraper.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Change this line
```

**Time zone conversion examples:**
- `0 0 * * *` - Midnight UTC (5:30 AM IST)
- `30 1 * * *` - 1:30 AM UTC (7:00 AM IST)
- `0 12 * * *` - Noon UTC (5:30 PM IST)

Use [Crontab Guru](https://crontab.guru/) to create custom schedules.

## 🎨 Customization

### Add More Job Keywords

Edit `.env` or GitHub Secrets `KEYWORDS`:
```
KEYWORDS=react developer,node.js developer,django developer,flutter developer,android developer,ios developer
```

### Add More Locations

Edit `.env` or GitHub Secrets `LOCATIONS`:
```
LOCATIONS=Chennai,Kolkata,Ahmedabad,Jaipur,Remote,Work from home
```

### Change Filter Criteria

Edit `scrapers/base_scraper.py` to modify:
- Technical keywords (line 30-35)
- Excluded keywords (line 38-41)
- Fresher indicators (line 49-53)

## 📧 Email Previews

The emails include:
- Total number of new jobs
- Jobs grouped by source (Naukri, LinkedIn, Internshala)
- Each job shows:
  - Title with direct link
  - Company name
  - Location
  - Posted date
  - "Apply Now" button
- Pro tips for job hunting success

## 🔧 Troubleshooting

### "Authentication failed" error
- Make sure you're using an **App Password**, not your regular Gmail password
- Check that 2-Factor Authentication is enabled on your Google account

### No jobs found
- The scrapers look for jobs posted in the last 24 hours only
- Try running at different times of day (more jobs post in mornings)
- Some keywords might not have fresh postings every day

### Jobs not matching criteria
- Check and adjust the `KEYWORDS` in your `.env` file
- Modify filters in `scrapers/base_scraper.py`

### GitHub Actions not running
- Check if Actions are enabled in your repository settings
- Verify all secrets are added correctly
- Check the Actions tab for error logs

## 📝 Project Structure

```
job-scraper/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py       # Base class with filtering logic
│   ├── naukri_scraper.py     # Naukri.com scraper
│   ├── linkedin_scraper.py   # LinkedIn scraper
│   └── internshala_scraper.py # Internshala scraper
├── utils/
│   ├── __init__.py
│   └── deduplicator.py       # Deduplication logic
├── email_notifier.py          # Email sending functionality
├── main.py                    # Main orchestration script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── .github/
    └── workflows/
        └── daily-scraper.yml  # GitHub Actions workflow
```

## 🎯 Next Steps for Landing a Job

While this tool helps you **never miss opportunities**, landing a job requires:

1. **Optimize Your Resume**
   - Tailor it for each application
   - Highlight projects and skills
   - Use keywords from job descriptions

2. **Apply Fast**
   - Apply within 2-4 hours of posting
   - Early applications get more attention

3. **Network**
   - Connect with employees on LinkedIn
   - Join tech communities
   - Attend virtual meetups

4. **Practice**
   - Solve coding problems daily
   - Practice system design
   - Prepare for behavioral interviews

5. **Follow Up**
   - Send thank-you emails after interviews
   - Check application status after a week

## 🤝 Contributing

Feel free to:
- Add more job board scrapers
- Improve filtering logic
- Enhance email templates
- Add new features

## ⚠️ Disclaimer

- This tool is for educational purposes
- Respect websites' robots.txt and terms of service
- Use reasonable delays between requests
- Some websites may block automated access

## 📄 License

MIT License - Feel free to use and modify for your job search!

## 💡 Tips

- Run manually first to verify everything works
- Check spam folder for first few emails
- Adjust keywords based on your interests
- Be patient - quality opportunities take time
- Apply to 10-15 jobs daily for best results

---

**Good luck with your job search! 🚀**

Remember: This tool gives you an edge by ensuring you never miss fresh opportunities, but your skills, resume, and interview prep are what will land you the job. Stay consistent and keep improving!
