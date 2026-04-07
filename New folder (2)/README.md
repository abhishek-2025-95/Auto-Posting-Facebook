# AI Comic Generator

A Python tool that automatically converts news articles into mobile-friendly 4-panel comic strips using AI.

## Features

- **Web Scraping**: Extracts clean article content from news URLs
- **AI Scriptwriting**: Uses Google Gemini to create structured 4-panel comic scripts
- **Image Generation**: Generates consistent comic panel images using free image generation APIs (Hugging Face Stable Diffusion)
- **Mobile-Friendly Output**: Creates responsive HTML pages optimized for mobile viewing

## Architecture

The tool follows a 4-step pipeline:

1. **The Extractor**: Scrapes news articles using `newspaper3k`
2. **The Director**: Uses Google Gemini to convert news into comic scripts
3. **The Artist**: Generates panel images using free image generation APIs (Hugging Face Stable Diffusion)
4. **The Publisher**: Assembles everything into mobile-friendly HTML

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up your Gemini API key**:

   You only need one API key:
   - **Gemini API key** (required) - for script generation
   - **Image generation** uses free APIs - no additional key needed!

   Option A: Set environment variable
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-gemini-api-key-here"
   
   # Windows CMD
   set GEMINI_API_KEY=your-gemini-api-key-here
   
   # Linux/Mac
   export GEMINI_API_KEY="your-gemini-api-key-here"
   ```

   Option B: Create a `config.txt` file:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
   
   **Note**: Your Gemini API key is already saved to `config.txt` and ready to use!

## Usage

### Basic Usage

```bash
python main.py "https://example.com/news-article"
```

### Specify Output Directory

```bash
python main.py "https://example.com/news-article" -o my_comics
```

### Provide API Key Directly

```bash
python main.py "https://example.com/news-article" --gemini-key your-gemini-key
```

## Output

The tool generates:
- `output/panel_1.png` through `output/panel_4.png` - Individual panel images
- `output/comic.html` - Mobile-friendly HTML file with all panels

Open `comic.html` in any web browser to view the comic. The HTML is optimized for mobile devices with responsive design.

## Cost Considerations

Each comic generation uses:
- 1 Google Gemini API call (for script generation) - **Free tier available**
- 4 image generations using free Hugging Face Stable Diffusion API - **Completely free!**

Estimated cost per comic: **$0.00** (completely free with Gemini free tier). Image generation uses free public APIs.

## Requirements

- Python 3.7+
- Google Gemini API key (for script generation) - [Get one here](https://makersuite.google.com/app/apikey)
- Internet connection (for web scraping and API calls)
- **No OpenAI key needed** - image generation uses free APIs!

## Troubleshooting

### "Failed to extract news content"
- The URL might not be accessible or the article format isn't supported
- Try a different news source

### "Gemini API key not found"
- Make sure you've set the `GEMINI_API_KEY` environment variable or added it to `config.txt`
- The Gemini API key is required for script generation
- Image generation uses free APIs and doesn't require additional keys

### "Failed to generate all panels"
- Free image generation APIs may have rate limits - wait a few seconds between runs
- If Hugging Face models are loading, the tool will automatically retry with different models
- Check your internet connection

### Images not displaying in HTML
- Make sure the image files are in the same directory as the HTML file (or adjust paths)
- Check that images were successfully generated

## Example

```bash
python main.py "https://apnews.com/article/example-news-story"
```

This will:
1. Scrape the article
2. Generate a 4-panel script
3. Create 4 comic panel images
4. Generate `output/comic.html`

Open `output/comic.html` in your browser to see the result!

## Notes

- **Visual Consistency**: DALL-E 3 doesn't maintain perfect character consistency across panels. The prompts are designed to maximize consistency, but some variation is expected.
- **Accuracy**: Always review generated content for factual accuracy before publishing.
- **Rate Limits**: OpenAI APIs have rate limits. For multiple comics, add delays between generations.

## License

This tool is provided as-is for educational and personal use.

