# enhanced_config.py - Enhanced configuration with token management
# Store your secret API keys here

# Google AI Studio (Gemini) API Key
GEMINI_API_KEY = "AIzaSyD9Lu0X_gjIaBPnEuJ7o3WqPoXFJI4jwQs"

# News API Key (Using Newsdata.io)
# Get a key at: https://newsdata.io/
NEWS_API_KEY = "pub_3ac6c917980e4981b60a108d498e3328"

# Facebook Graph API Configuration
FACEBOOK_ACCESS_TOKEN = "EAALzkWlQI4YBP5ytHKSdxpI1g2HlAB8ZAWReKO0z5GlYHDpKXKnBP514kb8VnLJYRCG4rori2pp1smUxEi6nJxSuCcEvAWUL9ZCQ9Uc7IUCq49Ss4YZCTyYYeaBhSXmPDqe8ZBBbvQTSzZC6mRcs1C0udi7JSak3h6whkX47ZBBNAe4PlFPXTZA5TzXlEt4i2zzzrn7ijhf6CZAGbU6szUSF5sqI3w7fZAzQlbnl9mJxj"
FACEBOOK_PAGE_ID = "758737463999000"  # Your existing page ID

# Facebook App Configuration (for token refresh)
# Get these from your Facebook Developer App
FACEBOOK_APP_ID = "YOUR_FACEBOOK_APP_ID_HERE"
FACEBOOK_APP_SECRET = "YOUR_FACEBOOK_APP_SECRET_HERE"

# Token Management Configuration
TOKEN_REFRESH_DAYS_BEFORE_EXPIRY = 7  # Refresh token 7 days before expiry
TOKEN_VALIDATION_INTERVAL_HOURS = 24  # Check token every 24 hours
AUTOMATIC_TOKEN_REFRESH = True  # Enable automatic token refresh

# Google Cloud Platform Configuration for Vertex AI (Imagen)
GCP_PROJECT_ID = "YOUR_GCP_PROJECT_ID_HERE"
GCP_LOCATION = "us-central1"

# News API Configuration
NEWS_LANGUAGE = "en"
NEWS_COUNTRIES = ["us"]  # Focus on US breaking news only
NEWS_HOURS_BACK = 12  # Look for news from last 12 hours

# Posting Schedule Configuration
POSTS_PER_DAY = 10
MINUTES_BETWEEN_POSTS = 144  # 24 hours / 10 posts = 2.4 hours = 144 minutes

# Image Generation Configuration
IMAGE_ASPECT_RATIO = "4:3"  # or "1:1" for square
IMAGE_QUALITY = "high"

# Token Management Settings
TOKEN_MONITORING_ENABLED = True
TOKEN_ALERT_EMAIL = "your-email@example.com"  # Optional: email alerts
TOKEN_BACKUP_ENABLED = True
TOKEN_ENCRYPTION_ENABLED = False  # Set to True for production


