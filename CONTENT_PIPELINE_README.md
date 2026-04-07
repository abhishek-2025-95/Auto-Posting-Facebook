# The Unseen Economy - Viral Content Pipeline

## 🚀 Overview
This pipeline generates complete viral content packages including:
- Shocking economic data points
- AI-generated images (DALL-E 3)
- Strategic engagement hooks
- UTM-tracked links
- Ready-to-post content

## 📋 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your_openai_api_key_here"

# Windows CMD
set OPENAI_API_KEY=your_openai_api_key_here

# Linux/Mac
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 3. Run the Pipeline
```bash
python content_pipeline.py
```

## 📊 Output
The script generates a JSON file with:
- **viral_take**: Shocking economic statement
- **dalle_image_prompt**: AI-generated image description
- **image_url**: DALL-E 3 generated image URL
- **utm_link**: Tracked link for analytics
- **final_post_text**: Complete post ready for Facebook

## 🎯 Content Strategy
- **Target**: US/Europe Millennials/Gen Z
- **Tone**: Angry, provocative, data-driven
- **Focus**: Economic justice, inequality, corporate greed
- **Format**: Controversial takes + engagement hooks + tracked links

## 📈 Analytics
All generated content includes UTM tracking:
- **Source**: Facebook
- **Medium**: Social
- **Campaign**: ViralOctober
- **Content**: ShockingData, RealityCheck, Controversial

## 🔄 Usage Examples

### Generate Single Content Package
```bash
python content_pipeline.py
```

### Integrate with Facebook Posting
```bash
# Generate content
python content_pipeline.py

# Post to Facebook (using existing cli.py)
python cli.py post-text "$(python -c "import json; print(json.load(open('generated_content.json'))['final_post_text'])")"
```

## 🎨 Customization
Edit `content_pipeline.py` to modify:
- Engagement hooks
- Hashtag strategies
- UTM parameters
- Content themes
- Image styles

## 💡 Tips
- Run multiple times for different content variations
- Save generated content for later use
- A/B test different engagement hooks
- Monitor UTM analytics for performance




