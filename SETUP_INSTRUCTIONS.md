# 🤖 Viral News Automation System - Setup Instructions

## 🎯 System Overview
Automated Python system that posts 5 times per day:
- Finds the most viral breaking news for US/EU markets
- Generates professional-grade images using AI
- Writes expert-level captions with hashtags
- Posts to Facebook automatically

## 📋 Prerequisites

### 1. API Keys Required
- **Google AI Studio (Gemini)**: ✅ Already configured
- **News API**: Get from https://newsapi.org/ (free tier available)
- **Facebook Graph API**: ✅ Already configured
- **Google Cloud Platform**: For Vertex AI Imagen (optional)

### 2. Python Environment
- Python 3.8+ installed
- All dependencies in requirements.txt

## 🚀 Quick Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Keys
Edit `config.py` and set your API keys:

```python
# Get from https://newsapi.org/
NEWS_API_KEY = "your_news_api_key_here"

# Your existing Facebook token (already set)
FACEBOOK_ACCESS_TOKEN = "your_facebook_token_here"

# For Vertex AI Imagen (optional)
GCP_PROJECT_ID = "your_gcp_project_id"
```

### Step 3: Test the System
```bash
python main.py
```

## 🔧 Detailed Configuration

### News API Setup
1. Go to https://newsapi.org/
2. Sign up for free account
3. Get your API key
4. Add to config.py

### Google Cloud Setup (Optional - for Imagen)
1. Create GCP project
2. Enable Vertex AI API
3. Create service account
4. Download JSON key file
5. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

## 📁 File Structure
```
├── main.py                 # Main orchestrator
├── config.py              # API keys and configuration
├── news_fetcher.py        # Fetch trending news
├── content_generator.py   # Generate captions and images
├── facebook_poster.py     # Post to Facebook
├── requirements.txt       # Python dependencies
└── automation_log.txt     # System logs (auto-created)
```

## ⚙️ How It Works

### 1. News Fetching
- Fetches top 5 breaking news from last 6 hours
- Targets US/EU markets
- Uses NewsAPI.org

### 2. Viral Selection
- Uses Gemini AI to analyze viral potential
- Considers visual potential, emotional impact
- Selects most shareable story

### 3. Content Generation
- **Caption**: Professional 100-150 word post with hashtags
- **Image**: AI-generated using Gemini + Vertex AI Imagen
- **Fallbacks**: Text-only posts if image generation fails

### 4. Facebook Posting
- Posts to your Facebook Page
- Includes image and caption
- Automatic error handling

### 5. Scheduling
- 5 posts per day (every 4.8 hours)
- Specific times: 6 AM, 10:30 AM, 3 PM, 7:30 PM, 10 PM
- Runs continuously

## 🎛️ Customization

### Change Posting Frequency
Edit `config.py`:
```python
POSTS_PER_DAY = 5  # Change to desired number
MINUTES_BETWEEN_POSTS = 288  # 24 hours / posts per day
```

### Modify News Sources
Edit `news_fetcher.py` to change:
- News sources
- Time range
- Keywords
- Regions

### Adjust Content Style
Edit `content_generator.py` to change:
- Caption tone
- Image style
- Hashtag strategy

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check all keys in config.py
   - Verify API quotas and billing

2. **Image Generation Fails**
   - System will post text-only content
   - Check Vertex AI setup

3. **Facebook Posting Fails**
   - Verify page permissions
   - Check access token validity

4. **News API Fails**
   - System uses fallback news
   - Check API key and quota

### Logs
Check `automation_log.txt` for:
- Successful posts
- Failed attempts
- Error details

## 🔄 Running the System

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
# Run in background
nohup python main.py &

# Or use systemd/cron
```

### Stop the System
Press `Ctrl+C` or kill the process

## 📊 Monitoring

### Check Logs
```bash
tail -f automation_log.txt
```

### View Facebook Posts
- Check your Facebook Page
- Posts include timestamps and IDs

### System Status
- Console shows real-time status
- Logs track all activity

## 🎉 Success!

Once running, your system will:
- ✅ Automatically find viral news
- ✅ Generate professional content
- ✅ Post to Facebook 5 times daily
- ✅ Handle errors gracefully
- ✅ Log all activity

**Your viral news automation system is ready!** 🚀



